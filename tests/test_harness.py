import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harness.protocol import Client, public_frame, public_batch
from harness.records import digest, summarize, wilson, write_json
from harness.publish import archive, verified_inventory
from harness.arena import PolicyProcess, policy_binary_hashes


class HarnessTests(unittest.TestCase):
    def test_research_executable_is_hashed_and_changes_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / 'policy'
            executable.write_bytes(b'first build')
            registry = {'test': {'command': ['{root}/policy']}}
            before = policy_binary_hashes(root, root, 'http://unused', ['test', 'test'], registry)
            self.assertEqual(list(before), ['test'])
            self.assertEqual(before['test']['sha256'], digest(executable))
            executable.write_bytes(b'second build')
            after = policy_binary_hashes(root, root, 'http://unused', ['test'], registry)
            self.assertNotEqual(before, after)

    def test_public_tape_excludes_research_spectator_extras_without_losing_cursor(self):
        batch = {'sequence': 4, 'timestamp_ms': 8, 'events': [
            {'type': 'theft_details', 'resource': 'ore'},
            {'type': 'message', 'to': [1], 'message': {'text': 'private'}},
            {'type': 'rule', 'event': {'type': 'built_city', 'player': 0}},
            {'type': 'message', 'to': None, 'message': {'text': 'public'}},
        ]}
        result = public_batch(batch)
        self.assertEqual(result['sequence'], 4)
        self.assertEqual([e['type'] for e in result['events']], ['rule', 'message'])
        self.assertEqual(len(batch['events']), 4)

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

    def test_capture_retains_only_public_roster_fields(self):
        view = {'version': 5, 'game': {'seat': None, 'own': None, 'legal_actions': []},
                'research_hands': ['PRIVATE'], 'host_token': 'SECRET', 'members': [
                    {'seat': 0, 'name': 'Juniper', 'connected': True, 'ready': False,
                     'is_you': False, 'subject': 'PRIVATE'},
                    {'seat': None, 'name': 'Spectator', 'connected': True}]}
        frame = public_frame(view)
        self.assertEqual(frame['members'], [{'seat': 0, 'name': 'Juniper', 'connected': True, 'ready': False}])
        self.assertNotIn('PRIVATE', json.dumps(frame))
        self.assertNotIn('SECRET', json.dumps(frame))

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


class ReplayActivityTests(unittest.TestCase):
    def test_public_replay_keeps_actions_and_chat_but_excludes_private_extras(self):
        from harness.replay import public_activity
        events = [
            {'type': 'rule', 'event': {'type': 'bought_development', 'player': 0}},
            {'type': 'rule', 'event': {'type': 'played_development', 'player': 1, 'card': 'road_building'}},
            {'type': 'message', 'from': 0, 'to': None, 'message': {'intent': 'chat', 'text': 'This funds your road.'}},
            {'type': 'message', 'from': 1, 'to': [0], 'message': {'intent': 'chat', 'text': 'PRIVATE MESSAGE'}},
            {'type': 'theft_details', 'player': 0, 'victim': 1, 'resource': 'ore'},
            {'type': 'rule', 'event': {'type': 'stole', 'player': 0, 'victim': 1, 'count': 1}},
        ]
        activity = public_activity([{'sequence': 12, 'timestamp_ms': 200, 'events': events}])
        self.assertEqual(len(activity), 4)
        self.assertEqual([row['sequence'] for row in activity], [12] * 4)
        self.assertEqual(activity[1]['text'], 'Played road building.')
        self.assertEqual(activity[2]['kind'], 'message')
        self.assertNotIn('PRIVATE', json.dumps(activity))
        self.assertNotIn('ore', json.dumps(activity))
        self.assertIn('card type hidden', activity[0]['text'])

    def test_activity_is_bounded_by_observed_position_and_hashes_both_sources(self):
        from harness.replay import replay_activity
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'frames.jsonl').write_text('retained frame source')
            batches = [{'sequence': seq, 'timestamp_ms': seq * 100, 'events': [{'type': 'message', 'from': 0, 'message': {'intent': 'chat', 'text': f'Event {seq}'}}]} for seq in [2, 8, 20]]
            (folder / 'events.jsonl').write_text('\n'.join(json.dumps(batch) for batch in batches))
            replay = replay_activity(folder, 8)
            self.assertEqual([row['sequence'] for row in replay['activity']], [2, 8])
            self.assertEqual(replay['sources']['frames'], digest(folder / 'frames.jsonl'))
            self.assertEqual(replay['sources']['events'], digest(folder / 'events.jsonl'))

    def test_roster_uses_recorded_names_at_each_position_without_future_updates(self):
        from harness.replay import replay_positions, public_activity
        game = {'turn': 1, 'current': 0, 'phase': {'type': 'main'}, 'hexes': [], 'ports': [],
                'buildings': [], 'roads': [], 'robber': 0, 'bank': [19]*5, 'deck_count': 24,
                'longest_road': None, 'largest_army': None,
                'players': [{'seat': 0, 'points': 2, 'private_hand': ['SECRET']}, {'seat': 1, 'points': 2}]}
        batches = [
            {'sequence': 1, 'timestamp_ms': 100, 'events': [{'type': 'joined', 'seat': 0, 'name': 'Juniper'}, {'type': 'joined', 'seat': 1, 'name': 'Atlas'}]},
            {'sequence': 3, 'timestamp_ms': 300, 'events': [{'type': 'presence', 'seat': 0, 'name': 'Juniper', 'connected': False}]},
            {'sequence': 4, 'timestamp_ms': 400, 'events': [{'type': 'rule', 'event': {'type': 'stole', 'player': 1, 'victim': 0, 'count': 1}}, {'type': 'rule', 'event': {'type': 'rolled', 'player': 0, 'first': 3, 'second': 4}}]},
            {'sequence': 8, 'timestamp_ms': 800, 'events': [{'type': 'presence', 'seat': 0, 'name': 'Later name', 'connected': True}]},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            frames = [{'version': n, 'game': game} for n in (0, 2, 4)]
            frames.append({'version': 5, 'game': game, 'members': [{'seat': 0, 'name': 'Captured name', 'connected': True, 'ready': True, 'subject': 'SECRET'}]})
            for file, rows in [('frames.jsonl', frames), ('events.jsonl', batches)]:
                (folder / file).write_text('\n'.join(json.dumps(row) for row in rows))
            before = digest(folder / 'frames.jsonl')
            positions = replay_positions(folder, [0, 1, 2, 3])
            self.assertNotIn('name', positions[0]['players'][0])
            self.assertEqual(positions[1]['players'][0]['name'], 'Juniper')
            self.assertNotIn('connected', positions[1]['players'][0])
            self.assertFalse(positions[2]['players'][0]['connected'])
            self.assertEqual(positions[3]['players'][0]['name'], 'Captured name')
            self.assertNotIn('Later name', json.dumps(positions))
            self.assertNotIn('SECRET', json.dumps(positions))
            self.assertEqual(positions[1]['bank'], [19]*5)
            self.assertEqual(before, digest(folder / 'frames.jsonl'))
        activity = public_activity(batches)
        self.assertIn('Juniper', activity[0]['text'])
        self.assertEqual(activity[1]['dice'], [3, 4])
        self.assertEqual(activity[1]['action'], 'rolled')


if __name__ == '__main__':
    unittest.main()
