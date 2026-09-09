import json
from pathlib import Path
import tempfile
import unittest

from harness import engine


def row(seed, rotation, winner_slot, points):
    slots = [(seat + rotation) % 4 for seat in range(4)]
    seats = []
    for seat in range(4):
        seats.append({'seat': seat, 'label': 'x', 'points': points[slots[seat]], 'decisions': 10, 'decision_ms': 5.0,
                      'max_decision_ms': 1.0, 'invalid': 0, 'stalls': 0, 'forced': 0, 'offers': 0, 'offers_accepted': 0,
                      'accepted_others': 0, 'settlements_built': 1, 'cities_built': 1, 'roads_built': 2,
                      'development_bought': 0, 'bank_trades': 0, 'player_trades': 0, 'cards_discarded': 0,
                      'times_robbed': 0, 'effort': {'errors': 0}})
    winner_seat = slots.index(winner_slot)
    return {'seed': seed, 'rotation': rotation, 'slots': slots, 'winner_slot': winner_slot,
            'game': {'status': 'completed', 'winner': winner_seat, 'turns': 60, 'seats': seats}}


class EngineHarnessTests(unittest.TestCase):
    def test_summary_counts_slot_wins_and_paired_contrast(self):
        rows = [row(s, r, 0 if (s + r) % 2 == 0 else 1, [10, 8, 6, 5]) for s in range(4) for r in range(4)]
        summary = engine.summarize(rows, ['v2', 'eta', 'fast', 'eta'])
        self.assertEqual(summary['completed'], 16)
        self.assertEqual(summary['slots'][0]['wins'], 8)
        self.assertEqual(summary['slots'][1]['wins'], 8)
        self.assertAlmostEqual(summary['paired_contrast']['mean_win_difference'], 0.0)
        self.assertEqual(summary['paired_contrast']['seeds'], 4)
        self.assertEqual(summary['slots'][2]['completed'], 16)

    def test_registration_rejects_bad_seats_and_seed_ranges(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'log/studies').mkdir(parents=True)
            (root / 'log/studies/demo.toml').write_text('id = "log/demo"\nstatus = "active"\n')
            with self.assertRaises(ValueError):
                engine.register(root, ['v3', 'eta'], '0-3', 'h', 'd', study='log/demo')
            with self.assertRaises(ValueError):
                engine.register(root, ['v2', 'eta'], '5-3', 'h', 'd', study='log/demo')
            identifier = engine.register(root, ['v2:{"depth":2}', 'eta', 'fast', 'eta'], '0-3', 'h', 'd', study='log/demo')
            data = (root / 'experiments' / f'{identifier}.toml').read_text()
            self.assertIn('arena = "engine"', data)
            self.assertIn('games = 16', data)
            self.assertIn(json.dumps('v2:{"depth":2}'), data)


if __name__ == '__main__':
    unittest.main()
