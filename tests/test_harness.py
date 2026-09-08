import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harness.protocol import Client, public_frame
from harness.records import digest, summarize, wilson, write_json
from harness.publish import archive, verified_inventory
from harness.arena import PolicyProcess


class HarnessTests(unittest.TestCase):
    def test_retry_keeps_exact_envelope_after_ambiguous_commit(self):
        client = Client('http://unused')
        envelope = {'request_id': 'fixed', 'expected_version': 42, 'command': {'type': 'start'}}
        with patch.object(client, 'request', side_effect=[TimeoutError(), {'duplicate': True}]) as request, patch('time.sleep'):
            self.assertTrue(client.submit('game', envelope)['duplicate'])
        self.assertIs(request.call_args_list[0].args[2], envelope)
        self.assertIs(request.call_args_list[1].args[2], envelope)

    def test_rotation_and_duplicate_policies_do_not_double_count_games(self):
        matches = [
            {'status': 'completed', 'slots': [0, 1], 'winner': 0, 'points': [10, 7], 'turns': 30},
            {'status': 'completed', 'slots': [1, 0], 'winner': 0, 'points': [10, 8], 'turns': 40},
            {'status': 'censored', 'slots': [0, 1], 'winner': None},
        ]
        summary = summarize(matches, ['fast', 'fast'])
        self.assertEqual((summary['completed'], summary['incomplete']), (2, 1))
        for row in summary['players']:
            self.assertEqual((row['wins'], row['losses'], row['completed']), (1, 1, 2))
        self.assertEqual(summary['players'][0]['mean_points'], 9)
        self.assertEqual(summary['mean_turns'], 35)
        self.assertIsNone(wilson(0, 0))
        self.assertAlmostEqual(wilson(5, 10)[0], .236593, places=5)

    def test_player_observations_cannot_be_exported(self):
        with self.assertRaises(ValueError):
            public_frame({'version': 1, 'game': {'seat': 0, 'own': {'resources': [1]}, 'legal_actions': []}})
        self.assertEqual(public_frame({'version': 1, 'game': {'seat': None, 'own': None, 'legal_actions': []}})['version'], 1)

    def test_archive_excludes_credentials_and_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id = '12345678-1234-1234-1234-123456789012'
            folder = root / 'runs' / run_id
            folder.mkdir(parents=True)
            (folder / 'private').mkdir()
            (folder / 'private/token.jwt').write_text('secret')
            write_json(folder / 'summary.json', {'completed': 4})
            write_json(folder / 'inventory.json', {'summary.json': digest(folder / 'summary.json')})
            archive(root, run_id, root / 'bundles')
            import tarfile
            with tarfile.open(root / 'bundles' / f'{run_id}.tar.gz') as bundle:
                self.assertEqual(set(bundle.getnames()), {f'{run_id}/summary.json', f'{run_id}/inventory.json'})
            with self.assertRaises(FileExistsError):
                archive(root, run_id, root / 'bundles')
            (folder / 'summary.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'changed'):
                verified_inventory(folder)

    def test_stdio_policy_is_persistent_and_bounded(self):
        import sys
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'policy.py'
            script.write_text('import sys\nfor line in sys.stdin:\n print(\'null\', flush=True)\n')
            policy = PolicyProcess({'transport': 'stdio', 'command': [sys.executable, str(script)]}, {}, root, root / 'log')
            try:
                self.assertIsNone(policy.choose({'view': {}}, 2))
                self.assertIsNone(policy.choose({'view': {}}, 2))
            finally:
                policy.close()
            self.assertIsNotNone(policy.process.poll())

    def test_unresponsive_policy_cannot_block_writing_a_large_observation(self):
        import sys
        import time
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'policy.py'
            script.write_text('import time\ntime.sleep(60)\n')
            policy = PolicyProcess({'transport': 'stdio', 'command': [sys.executable, str(script)]}, {}, root, root / 'log')
            started = time.monotonic()
            try:
                with self.assertRaises(TimeoutError):
                    policy.choose({'view': 'x' * 1_000_000}, .1)
                self.assertLess(time.monotonic() - started, 2)
            finally:
                policy.close()


if __name__ == '__main__':
    unittest.main()
