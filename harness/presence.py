"""Keep a stdio seat connected while REST owns its decisions and event history.

This small WebSocket client only drains server frames and answers transport
pings. It never supplies observations to a policy or submits game commands.
"""
import base64
import hashlib
import os
import socket
import ssl
import struct
import threading
from urllib.parse import urlsplit


class SeatPresence:
    def __init__(self, base, game_id, token):
        address = urlsplit(base)
        if address.scheme not in ('http', 'https') or not address.hostname:
            raise ValueError('Presence needs an HTTP or HTTPS server address')
        if any(character in token for character in '\r\n'):
            raise ValueError('Invalid presence credential')
        self.closed = False
        self.error = None
        self.thread = None
        self.stream = None
        connection = socket.create_connection(
            (address.hostname, address.port or (443 if address.scheme == 'https' else 80)), timeout=10)
        self.socket = connection
        try:
            if address.scheme == 'https':
                self.socket = ssl.create_default_context().wrap_socket(connection, server_hostname=address.hostname)
            self.stream = self.socket.makefile('rb')
            key = base64.b64encode(os.urandom(16)).decode('ascii')
            path = address.path.rstrip('/') + f'/v1/games/{game_id}/ws'
            self.socket.sendall((
                f'GET {path} HTTP/1.1\r\nHost: {address.netloc}\r\n'
                'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n'
                'Sec-WebSocket-Protocol: settlers-v1\r\n'
                f'Authorization: Bearer {token}\r\n\r\n').encode('ascii'))
            status = self.stream.readline(8193)
            if len(status) > 8192 or status.split()[1:2] != [b'101']:
                raise ConnectionError('Game WebSocket did not accept the presence connection')
            headers, size = {}, len(status)
            while True:
                line = self.stream.readline(8193)
                size += len(line)
                if not line or size > 32768 or len(line) > 8192:
                    raise ConnectionError('Invalid game WebSocket response headers')
                if line == b'\r\n':
                    break
                name, separator, value = line.partition(b':')
                if not separator:
                    raise ConnectionError('Invalid game WebSocket response header')
                headers[name.strip().lower()] = value.strip()
            accept = base64.b64encode(hashlib.sha1(
                (key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('ascii')).digest())
            if (headers.get(b'sec-websocket-accept') != accept
                    or headers.get(b'upgrade', b'').lower() != b'websocket'
                    or b'upgrade' not in [part.strip().lower() for part in headers.get(b'connection', b'').split(b',')]
                    or headers.get(b'sec-websocket-protocol') != b'settlers-v1'):
                raise ConnectionError('Invalid game WebSocket handshake')
            self.socket.settimeout(None)
            self.thread = threading.Thread(target=self._drain, name='stdio-seat-presence', daemon=True)
            self.thread.start()
        except BaseException:
            self.close()
            raise

    def _read(self, size):
        data = self.stream.read(size)
        if len(data) != size:
            raise ConnectionError('Stdio seat WebSocket disconnected')
        return data

    def _send_control(self, opcode, payload=b''):
        mask = os.urandom(4)
        body = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self.socket.sendall(bytes([0x80 | opcode, 0x80 | len(payload)]) + mask + body)

    def _drain(self):
        try:
            while not self.closed:
                first, second = self._read(2)
                opcode, size = first & 15, second & 127
                if first & 0x70 or second & 0x80 or opcode not in (0, 1, 2, 8, 9, 10):
                    raise ConnectionError('Invalid game WebSocket frame')
                if size == 126:
                    size = struct.unpack('!H', self._read(2))[0]
                elif size == 127:
                    size = struct.unpack('!Q', self._read(8))[0]
                if size > 1_048_576 or (opcode >= 8 and (size > 125 or not first & 0x80)):
                    raise ConnectionError('Game WebSocket frame exceeds its limit')
                payload = self._read(size)
                if opcode == 8:
                    self._send_control(8, payload)
                    raise ConnectionError('Stdio seat WebSocket closed by server')
                if opcode == 9:
                    self._send_control(10, payload)
                # Snapshots, events, and fragments are drained, never policy input.
        except Exception as error:
            if not self.closed:
                self.error = error

    def check(self):
        if self.error is not None:
            raise ConnectionError(f'Stdio seat presence failed: {self.error}') from self.error

    def close(self):
        self.closed = True
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        if self.thread is not None:
            self.thread.join(timeout=3)
        if self.stream is not None:
            self.stream.close()
        self.socket.close()
