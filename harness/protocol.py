"""Small dependency-free REST client. A policy never receives another seat's token."""
import json
import time
import urllib.error
import urllib.request
import uuid


class ServerError(RuntimeError):
    def __init__(self, status, data):
        self.status, self.data = status, data
        super().__init__(f"HTTP {status}: {data.get('code', 'unknown')}: {data.get('message', '')}")


class Client:
    def __init__(self, base, token=None):
        self.base, self.token = base.rstrip('/'), token

    def request(self, method, path, data=None):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        request = urllib.request.Request(
            self.base + path, data=None if data is None else json.dumps(data).encode(),
            headers=headers, method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise ServerError(error.code, json.load(error)) from error

    @classmethod
    def guest(cls, base, name):
        auth = cls(base).request('POST', '/v1/auth/guest', {'name': name})
        return cls(base, auth['token'])

    def game(self, game_id):
        return self.request('GET', f'/v1/games/{game_id}')

    def submit(self, game_id, envelope):
        # Ambiguous failures must retry the SAME request UUID, version and command.
        for attempt in range(4):
            try:
                return self.request('POST', f'/v1/games/{game_id}/commands', envelope)
            except ServerError as error:
                if error.status != 503 or attempt == 3:
                    raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == 3:
                    raise
            time.sleep(.1 * 2 ** attempt)
        raise AssertionError('unreachable')

    def command(self, game_id, version, command):
        return self.submit(game_id, {
            'request_id': str(uuid.uuid4()), 'expected_version': version, 'command': command,
        })

    def history(self, game_id, after):
        return self.request('GET', f'/v1/games/{game_id}/events?after={after}&limit=100')


def public_frame(view):
    """Fail closed on a player view; export only spectator observations."""
    game = view.get('game')
    if not game:
        return None
    if game.get('own') is not None or game.get('seat') is not None or game.get('legal_actions'):
        raise ValueError('Replay capture requires a spectator view')
    return {'version': view['version'], 'game': game}
