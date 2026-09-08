"""One JSON observation in, one protocol Command (or null) out. Logs go to stderr."""
import json
import sys


def choose(view):
    game = view.get('game')
    if not game or not game['legal_actions']:
        return None
    # Avoid endless reciprocal bank trades. This intentionally weak policy does
    # not propose trades, search hidden state, or try to estimate strategic value.
    priorities = ['build_city', 'build_settlement', 'buy_development', 'play_knight',
                  'play_road_building', 'build_road', 'roll', 'discard', 'move_robber',
                  'finish_road_building', 'end_turn']
    actions = game['legal_actions']
    action = min(actions, key=lambda a: priorities.index(a['type']) if a['type'] in priorities else 99)
    return {'type': 'act', 'action': action}


if __name__ == '__main__':
    for line in sys.stdin:
        message = json.loads(line)
        print(json.dumps(choose(message['view'])), flush=True)
