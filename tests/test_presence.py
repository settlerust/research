import base64
import hashlib
from pathlib import Path
import socket
import struct
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from harness.presence import SeatPresence


def handshake(connection, *, valid=True):
    stream = connection.makefile('rb')
    request = stream.readline()
    headers = {}
    while (line := stream.readline()) != b'\r\n':
        key, value = line.split(b':', 1)
        headers[key.lower()] = value.strip()
    accept = base64.b64encode(hashlib.sha1(
        headers[b'sec-websocket-key'] + b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
    connection.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n'
                       b'Connection: keep-alive,Upgrade\r\nSec-WebSocket-Protocol: settlers-v1\r\n'
                       b'Sec-WebSocket-Accept: ' + (accept if valid else b'invalid') + b'\r\n\r\n')
    return request, headers, stream


class PresenceTests(unittest.TestCase):
    def test_stdio_seats_connect_and_mark_ready_before_the_host_starts(self):
        from harness.arena import match
        connected, ready, joined, closed = set(), set(), [], []
        state = {'started': False}

        class Client:
            def __init__(self, seat):
                self.seat, self.token = seat, str(seat)

            def request(self, *_args):
                return {'id': 'test-game'}

            def game(self, _game_id):
                game = ({'phase': {'type': 'finished', 'winner': 0}, 'turn': 1,
                         'players': [{'points': 10}, {'points': 2}],
                         'own': None, 'seat': None, 'legal_actions': []}
                        if state['started'] else None)
                return {'version': 1, 'game': game, 'members': [
                    {'seat': seat, 'connected': seat in connected, 'ready': seat in ready}
                    for seat in joined]}

            def command(self, _game_id, _version, command):
                if command['type'] == 'join_agent':
                    joined.append(self.seat)
                elif command['type'] == 'set_ready':
                    if self.seat not in connected:
                        raise RuntimeError('Server requires a connection before readiness')
                    ready.add(self.seat)
                elif command['type'] == 'start':
                    if ready != {0, 1} or connected != {0, 1}:
                        raise RuntimeError('Server requires all seats connected and ready')
                    state['started'] = True

            def history(self, *_args):
                return {'events': [{'sequence': 1, 'events': []}], 'next_after': 1,
                        'current_version': 1}

        class Presence:
            def __init__(self, _base, _game_id, token):
                self.seat = int(token)
                connected.add(self.seat)

            def check(self):
                pass

            def close(self):
                closed.append(self.seat)

        class Policy:
            transport = 'stdio'
            process = SimpleNamespace(poll=lambda: None)

            def __init__(self, *_args):
                pass

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = {'base': 'http://localhost', 'run_id': 'test', 'server': str(root),
                    'players': ['example', 'example'], 'settings': {'players': 2},
                    'match_seconds': 5, 'max_turns': 100, 'max_decisions': 100,
                    'decision_seconds': 1}
            with patch('harness.arena.Client.guest', side_effect=[Client(None), Client(0), Client(1)]), \
                    patch('harness.arena.SeatPresence', Presence), patch('harness.arena.PolicyProcess', Policy):
                result = match(root, root, 0, [0, 1], plan, {'example': {}}, {})
        self.assertEqual(result['status'], 'completed', result.get('error'))
        self.assertTrue(state['started'])
        self.assertEqual(sorted(closed), [0, 1])

    def test_authenticates_drains_frames_answers_masked_ping_and_closes(self):
        client, server = socket.socketpair()
        server.settimeout(3)
        received, pong_seen = {}, threading.Event()

        def serve():
            try:
                request, headers, stream = handshake(server)
                received.update(request=request, headers=headers)
                # Ignore long snapshots and fragments; only ping needs a reply.
                server.sendall(b'\x81\x7e' + struct.pack('!H', 130) + b'x' * 130
                               + b'\x01\x01a\x80\x01b\x89\x04ping')
                first, second = stream.read(2)
                mask, payload = stream.read(4), stream.read(second & 127)
                received['pong'] = (first, second, bytes(value ^ mask[i % 4] for i, value in enumerate(payload)))
                pong_seen.set()
                received['closed'] = stream.read(1) == b''
                stream.close()
            finally:
                server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        with patch('harness.presence.socket.create_connection', return_value=client):
            presence = SeatPresence('http://localhost:5555', 'test-game', 'seat-only-token')
        try:
            self.assertTrue(pong_seen.wait(2))
            presence.check()
            self.assertEqual(received['request'], b'GET /v1/games/test-game/ws HTTP/1.1\r\n')
            self.assertEqual(received['headers'][b'authorization'], b'Bearer seat-only-token')
            self.assertEqual(received['pong'], (0x8a, 0x84, b'ping'))
        finally:
            presence.close()
            thread.join(timeout=3)
        self.assertFalse(presence.thread.is_alive())
        self.assertFalse(thread.is_alive())
        self.assertTrue(received['closed'])

    def test_bad_handshake_is_rejected_and_connection_is_closed(self):
        client, server = socket.socketpair()

        def serve():
            _, _, stream = handshake(server, valid=False)
            stream.close()
            server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        with patch('harness.presence.socket.create_connection', return_value=client):
            with self.assertRaisesRegex(ConnectionError, 'handshake'):
                SeatPresence('http://localhost:5555', 'test-game', 'token')
        thread.join(timeout=3)
        self.assertEqual(client.fileno(), -1)

    def test_disconnect_and_oversized_frames_fail_the_run(self):
        for response in (b'', b'\x81\x7f' + struct.pack('!Q', 1_048_577)):
            with self.subTest(response=response):
                client, server = socket.socketpair()

                def serve():
                    _, _, stream = handshake(server)
                    server.sendall(response)
                    stream.close()
                    server.close()

                thread = threading.Thread(target=serve, daemon=True)
                thread.start()
                with patch('harness.presence.socket.create_connection', return_value=client):
                    presence = SeatPresence('http://localhost:5555', 'test-game', 'token')
                try:
                    deadline = time.monotonic() + 2
                    while presence.error is None and time.monotonic() < deadline:
                        time.sleep(.01)
                    with self.assertRaisesRegex(ConnectionError, 'presence failed'):
                        presence.check()
                finally:
                    presence.close()
                    thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
