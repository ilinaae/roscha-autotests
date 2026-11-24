import select
import socket
import struct
import subprocess
import sys
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

from core.config import ConfigurationError
from core.diagnostics import LOGGER


def resolve_wifi_interface(option):
    if sys.platform != 'win32':
        raise ConfigurationError('Режим --wifi-interface доступен на Windows.')
    if option != 'auto' and (not option.isascii() or not option.isdecimal() or len(option) > 10
                             or not 1 <= int(option) <= 0xFFFFFFFF):
        raise ConfigurationError('Укажи --wifi-interface auto или числовой индекс Wi-Fi.')

    # InterfaceType 71 is IEEE 802.11, independent of the Windows display language.
    command = """
    $ErrorActionPreference = 'Stop'
    $adapters = Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceType -eq 71 }
    foreach ($adapter in $adapters) {
        $ip = Get-NetIPConfiguration -InterfaceIndex $adapter.ifIndex
        if ($ip.IPv4Address -and $ip.IPv4DefaultGateway) { $adapter.ifIndex }
    }
    """
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                capture_output=True, text=True, errors='replace', timeout=20, check=True)
    except (OSError, subprocess.SubprocessError):
        raise ConfigurationError('Windows не удалось получить список Wi-Fi-адаптеров.') from None
    indices = [int(line.strip()) for line in result.stdout.splitlines() if line.strip().isdecimal()]
    if not indices:
        raise ConfigurationError('Подключи компьютер к Wi-Fi. Windows не нашла активный адаптер с IPv4-шлюзом.')
    if option == 'auto' and len(indices) == 1:
        return indices[0]
    available = ', '.join(map(str, indices))
    if option == 'auto':
        raise ConfigurationError(f'Активно несколько Wi-Fi-адаптеров. Укажи --wifi-interface с одним из индексов: {available}.')
    index = int(option)
    if index not in indices:
        raise ConfigurationError(f'Индекс {index} сейчас не относится к подключённому Wi-Fi. '
                                 f'Используй --wifi-interface auto. Активные индексы: {available}.')
    return index


@contextmanager
def direct_wifi_proxy(base_url, interface_index):
    """Loopback CONNECT proxy for the shop. TLS remains between Chromium and the site."""
    site = urlsplit(base_url)
    if sys.platform != 'win32' or site.scheme != 'https' or site.port not in (None, 443):
        raise ConfigurationError('Прямой Wi-Fi доступен на Windows для HTTPS-сайта на порту 443.')
    hosts = {site.hostname}
    if site.hostname in {'roscha.net', 'www.roscha.net'}:
        hosts.update({'roscha.net', 'www.roscha.net'})

    class WifiTunnel(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_CONNECT(self):
            host, _, port = self.path.rpartition(':')
            if host.lower() not in hosts or port != '443':
                self.send_error(403)
                return

            connected = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as upstream:
                    upstream.settimeout(12)
                    # Winsock IP_UNICAST_IF uses an IPv4 interface index in network byte order.
                    upstream.setsockopt(socket.IPPROTO_IP, getattr(socket, 'IP_UNICAST_IF', 31),
                                        struct.pack('!I', interface_index))
                    upstream.connect((socket.gethostbyname(host), 443))
                    self.send_response(200, 'Connection Established')
                    self.end_headers()
                    connected = True
                    self.connection.settimeout(12)
                    self.relay(upstream)
            except OSError as exc:
                if not connected:
                    LOGGER.warning('Прямое соединение с сайтом не установлено (%s).', type(exc).__name__)
                    try:
                        self.send_error(502)
                    except OSError:
                        pass

        def relay(self, upstream):
            while True:
                ready, _, _ = select.select((upstream, self.connection), (), (), 60)
                if not ready:
                    return
                for source in ready:
                    chunk = source.recv(65536)
                    if not chunk:
                        return
                    destination = self.connection if source is upstream else upstream
                    destination.sendall(chunk)

    with ThreadingHTTPServer(('127.0.0.1', 0), WifiTunnel) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}'
        finally:
            server.shutdown()
            thread.join()
