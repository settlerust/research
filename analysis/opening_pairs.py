"""Read the setup placements of the traced opening/planner-tables games and report each
arm's chosen pairs with their per-resource pips. The board geometry is the engine's fixed
topology (crates/engine/src/topology.rs), replicated here so a site's pips can be
computed from the packed hex bytes the trace records: low nibble resource + 1, high
nibble dice total."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ['brick', 'lumber', 'wool', 'grain', 'ore']
CORNERS = [(0, -2), (1, -1), (1, 1), (0, 2), (-1, 1), (-1, -1)]


def topology():
    """Vertices and their incident hexes, in the engine's numbering."""
    axial = [(q, r) for r in range(-2, 3) for q in range(-2, 3) if abs(q + r) <= 2]
    centers = [[2 * q + r, 3 * r] for q, r in axial]
    points = sorted({(x + dx, y + dy) for x, y in centers for dx, dy in CORNERS})
    ids = {p: i for i, p in enumerate(points)}
    incident = [[] for _ in points]
    for h, (x, y) in enumerate(centers):
        for dx, dy in CORNERS:
            incident[ids[(x + dx, y + dy)]].append(h)
    return incident


INCIDENT = topology()


def pips(number):
    return 6 - abs(number - 7) if 2 <= number <= 12 and number != 7 else 0


def site_pips(hexes, vertex):
    """Per-resource pips of the hexes touching a vertex."""
    out = [0.0] * 5
    for h in INCIDENT[vertex]:
        byte = hexes[h]
        resource = (byte & 15) - 1
        if 0 <= resource <= 4:
            out[resource] += pips(byte >> 4)
    return out


def chosen_pairs(rows, slot):
    """Chosen setup settlement vertices and their per-resource pips for one seat."""
    games = []
    for r in rows:
        if r['game']['status'] != 'completed':
            continue
        hexes = r['game']['trace'][0]['position']['hexes']
        settlements, notes = [], []
        for entry in r['game']['trace']:
            if r['slots'][entry['seat']] != slot or entry['phase'].get('type') != 'setup_settlement':
                continue
            vertex = entry['chosen']['action']['vertex']
            settlements.append(vertex)
            note = None
            for candidate in entry['candidates']:
                if candidate['action'] and candidate['action'].get('vertex') == vertex:
                    note = candidate.get('note')
                    break
            notes.append(note)
        pair = [site_pips(hexes, v) for v in settlements]
        numbers = sorted({hexes[h] >> 4 for v in settlements for h in INCIDENT[v]
                          if (hexes[h] & 15) > 0 and (hexes[h] >> 4) != 7})
        games.append({'seed': r['seed'], 'slot': slot, 'vertices': settlements,
                      'pips': [sum(p[i] for p in pair) for i in range(5)],
                      'numbers': numbers,
                      'notes': notes})
    return games


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('games', nargs='+', help='traced games.jsonl (candidate run, then its control-half run)')
    parser.add_argument('--slot', type=int, default=0, help='slot of the seat to read')
    args = parser.parse_args()
    for path in args.games:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        for game in chosen_pairs(rows, args.slot):
            pips_text = ', '.join(f'{p:.0f} {name}' for name, p in zip(RESOURCES, game['pips']) if p > 0)
            print(f"seed {game['seed']} slot {game['slot']}: sites {game['vertices']} give {pips_text} pips, "
                  f"{len(game['numbers'])} distinct numbers {game['numbers']}")
            for note in game['notes']:
                if note:
                    print(f'  {note}')
        games = chosen_pairs(rows, args.slot)
        means = [sum(g['pips'][i] for g in games) / len(games) for i in range(5)]
        print('mean pips: ' + ', '.join(f'{p:.1f} {name}' for name, p in zip(RESOURCES, means)))


if __name__ == '__main__':
    main()
