"""Compact ordinary-spectator activity, derived only from verified event tapes."""
import json

from .protocol import public_batch
from .records import digest

RESOURCES = ['brick', 'lumber', 'wool', 'grain', 'ore']


def resources(values):
    return ', '.join(f'{count} {name}' for name, count in zip(RESOURCES, values) if count) or 'nothing'


def player_name(members, seat):
    return members.get(seat, {}).get('name', 'a player whose name was not recorded')


def update_members(members, event):
    seat = event.get('seat')
    if type(seat) is not int or not 0 <= seat < 4:
        return
    if event['type'] in ('joined', 'presence'):
        member = members.setdefault(seat, {})
        member['name'] = event['name']
        if 'connected' in event:
            member['connected'] = event['connected']
    elif event['type'] == 'ready_changed':
        members.setdefault(seat, {})['ready'] = event['ready']


def replay_positions(match_folder, indices):
    """Enrich selected observed boards with the roster known at each version."""
    source = [json.loads(line) for line in (match_folder / 'frames.jsonl').read_text().splitlines()]
    batches = [json.loads(line) for line in (match_folder / 'events.jsonl').read_text().splitlines()]
    members, cursor, frames = {}, 0, []
    fields = ['turn', 'current', 'phase', 'hexes', 'ports', 'buildings', 'roads', 'robber']
    player_fields = ['seat', 'resource_count', 'development_count', 'played_knights', 'settlements',
                     'cities', 'roads', 'points', 'road_length', 'victory_cards']
    for index in indices:
        frame = source[index]
        game = frame['game']
        if game.get('own') is not None or game.get('seat') is not None or game.get('legal_actions'):
            raise ValueError('Player observations cannot become public exhibits')
        while cursor < len(batches) and batches[cursor]['sequence'] <= frame['version']:
            for event in batches[cursor]['events']:
                update_members(members, event)
            cursor += 1
        # New captures carry the actual roster; older captures recover it from
        # joined/presence/ready events without changing the immutable source tape.
        for member in frame.get('members', []):
            members[member['seat']] = {key: member[key] for key in ('name', 'connected', 'ready') if key in member}
        players = []
        for player in game['players']:
            public = {key: player[key] for key in player_fields if key in player and player[key] is not None}
            public.update(members.get(player['seat'], {}))
            players.append(public)
        frames.append({'version': frame['version'], **{key: game[key] for key in fields}, 'players': players,
                       **{key: game[key] for key in ('bank', 'bank_available', 'deck_count', 'longest_road', 'largest_army') if key in game}})
    return frames


def describe_rule(event, members=None):
    members = members or {}
    name = lambda seat: player_name(members, seat)
    kind = event['type']
    if kind == 'phase_changed':
        return None
    if kind in ('built_settlement', 'built_city'):
        return f"Built a {kind.removeprefix('built_')} at vertex {event['vertex']}."
    if kind == 'setup_settlement_moved':
        return f"Moved a setup settlement from vertex {event['from']} to {event['vertex']}."
    if kind == 'built_road':
        return f"Built a road on edge {event['edge']}."
    if kind == 'rolled':
        return f"Rolled {event['first']} + {event['second']} = {event['first'] + event['second']}."
    if kind in ('produced', 'took_resources'):
        return f"Received {resources(event['resources'])}."
    if kind == 'discarded':
        return f"Discarded {event['count']} cards."
    if kind == 'robber_moved':
        return f"Moved the robber to hex {event['hex']}."
    if kind == 'stole':
        return f"Stole {event['count']} card(s) from {name(event['victim'])}."
    if kind == 'bought_development':
        return 'Bought a development card (card type hidden).'
    if kind == 'played_development':
        return f"Played {event['card'].replace('_', ' ')}."
    if kind == 'monopoly_collected':
        return f"Collected {event['count']} {event['resource']} from {name(event['victim'])} with Monopoly."
    if kind in ('bank_traded', 'traded'):
        partner = 'the bank' if kind == 'bank_traded' else name(event['other'])
        return f"Traded {resources(event['give'])} for {resources(event['receive'])} with {partner}."
    if kind == 'awards_changed':
        return 'Awards: ' + '; '.join(f"{key.replace('_', ' ')}: " + (name(event[key]) if event.get(key) is not None else 'unclaimed') for key in ('longest_road', 'largest_army')) + '.'
    if kind == 'turn_changed':
        return f"Started turn {event['turn']}."
    if kind == 'won':
        return f"Won the game with {event['points']} points."
    if kind == 'timed_out':
        return 'Timed out; the server applied a fallback.'
    raise ValueError(f'Unrecognized public rule event: {kind}')


def communication(message):
    # Only documented public communication fields; never serialize unknown data.
    text = message.get('text')
    if text:
        return text
    return message['intent'].replace('_', ' ') + (f": {resources(message['resources'])}" if message.get('resources') else '')


def public_activity(source):
    activity = []
    offers = {}
    members = {}
    previous = -1
    for raw in source:
        if raw['sequence'] <= previous:
            raise ValueError('Public event sequence must increase')
        previous = raw['sequence']
        # Old immutable tapes can predate public filtering. Apply it again here.
        batch = public_batch(raw)
        for event in batch['events']:
            update_members(members, event)
            kind, player, text, category = event['type'], None, None, 'action'
            details = {'action': kind}
            if kind == 'rule':
                rule = event['event']
                player = rule.get('player')
                text = describe_rule(rule, members)
                details['action'] = rule['type']
                if rule['type'] == 'rolled':
                    details['dice'] = [rule['first'], rule['second']]
            elif kind == 'message':
                player, text, category = event['from'], communication(event['message']), 'message'
            elif kind == 'trade_offered':
                offer = event['offer']
                player = offer['from']
                offers[offer['id']] = player
                recipients = ', '.join(player_name(members, seat) for seat in offer['to'])
                text = f"Offered {resources(offer['give'])} for {resources(offer['receive'])} to {recipients}."
                if offer.get('message'):
                    # Trade offers and their attached explanations are public protocol events.
                    activity.append({'sequence': batch['sequence'], 'timestampMs': batch['timestamp_ms'], 'kind': 'message', 'player': player, 'text': communication(offer['message'])})
            elif kind == 'trade_rejected':
                player = event['player']
                proposer = offers.get(event['offer_id'])
                text = 'Declined a trade offer' + (f' from {player_name(members, proposer)}.' if proposer is not None else '.')
            elif kind == 'trade_closed':
                player = offers.get(event['offer_id'])
                text = f"Trade offer closed: {event['reason'].replace('_', ' ')}."
            elif kind == 'started':
                text = 'The game started.'
            if text is not None:
                activity.append({'sequence': batch['sequence'], 'timestampMs': batch['timestamp_ms'], 'kind': category,
                                 **({'player': player} if player is not None else {}), 'text': text, **details})
    return activity


def replay_activity(match_folder, final_version):
    path = match_folder / 'events.jsonl'
    source = [json.loads(line) for line in path.read_text().splitlines()]
    # This protocol records each event batch at its resulting room version.
    # Use the recorded sequence, never a timestamp guess, to bound the exhibit.
    activity = public_activity([batch for batch in source if batch['sequence'] <= final_version])
    if len(activity) > 6000:
        raise ValueError('Curated replay exceeds 6000 public activity entries')
    return {'activity': activity, 'sources': {'frames': digest(match_folder / 'frames.jsonl'), 'events': digest(path)}}
