import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

from harness.cli import register
from harness.notebook import canonical_root, cell, collect, new_study, study_path, sync, worktree


class NotebookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write('approaches/ports/README.mdx', '# Ports\n\nKeep this original proposal.\n')
        self.write('docs/roadmap.md', '# Roadmap\n\nKeep the open questions.\n')
        self.write('policies/registry.toml', '[eta]\ntransport = "stdio"\ncommand = ["policy"]\n')
        self.path = new_study(self.root, 'ports/exchange', 'Exchange timing', 'Does conversion help?')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def update(self, **fields):
        data = tomllib.loads(self.path.read_text()) | fields
        self.path.write_text(''.join(f'{key} = {json.dumps(value)}\n' for key, value in data.items()))

    def protocol(self):
        return register(self.root, ['eta', 'eta'], 4, 'An effect', 'A fixed rule', study='ports/exchange')

    def test_studies_have_one_existing_owner_and_cannot_overwrite(self):
        self.assertEqual(self.path, self.root / 'approaches/ports/studies/exchange.toml')
        self.assertEqual(new_study(self.root, 'log/plumbing', 'Plumbing', 'Does it work?'),
                         self.root / 'log/studies/plumbing.toml')
        for identifier in ['../escape', 'ports/../../escape', 'unknown/idea', 'ports']:
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                study_path(self.root, identifier)
        with self.assertRaises(FileExistsError):
            new_study(self.root, 'ports/exchange', 'Replacement', 'A different question')

    def test_registration_files_ownership_and_rejects_unknown_or_completed_studies(self):
        identifier = self.protocol()
        protocol = tomllib.loads((self.root / f'experiments/{identifier}.toml').read_text())
        self.assertEqual(protocol['study'], 'ports/exchange')
        self.assertEqual(collect(self.root)[0]['experiments'], [identifier])
        with self.assertRaisesRegex(ValueError, 'Unknown study'):
            register(self.root, ['eta', 'eta'], 4, 'Question', 'Rule', study='ports/missing')
        self.update(status='complete')
        with self.assertRaisesRegex(ValueError, 'complete'):
            self.protocol()

    def test_sync_is_deterministic_preserves_prose_and_detects_stale_sections(self):
        identifier = self.protocol()
        original = (self.root / f'experiments/{identifier}.toml').read_bytes()
        with self.assertRaisesRegex(ValueError, 'stale'):
            sync(self.root, check=True)
        _, changed = sync(self.root)
        self.assertEqual(len(changed), 3)
        self.assertTrue((self.root / 'approaches/ports/README.mdx').read_text().startswith('# Ports\n\nKeep this original proposal.'))
        self.assertEqual(sync(self.root, check=True)[1], [])
        self.update(outcome='The decision rule failed; keep the baseline.')
        with self.assertRaisesRegex(ValueError, 'stale'):
            sync(self.root, check=True)
        sync(self.root)
        self.assertIn('decision rule failed', (self.root / 'log/experiments.mdx').read_text())
        self.assertEqual((self.root / f'experiments/{identifier}.toml').read_bytes(), original)

    def test_legacy_protocols_remain_byte_identical_and_cannot_have_two_owners(self):
        path = self.write('experiments/old.toml', 'id = "old"\nhypothesis = "Original frozen question"\n')
        original = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Unfiled experiment'):
            collect(self.root)
        self.update(legacy_experiments=['old'])
        sync(self.root)
        self.assertEqual(path.read_bytes(), original)
        other = new_study(self.root, 'log/other', 'Other', 'Another question')
        other.write_text(other.read_text().replace('legacy_experiments = []', 'legacy_experiments = ["old"]'))
        with self.assertRaisesRegex(ValueError, 'two studies'):
            collect(self.root)

    def test_invalid_and_interrupted_runs_need_interpretation_too(self):
        identifier = self.protocol()
        self.write('records/runs/failed.md', f'# Failed\n\nStatus: **invalid**. Experiment: `{identifier}`.\n')
        with self.assertRaisesRegex(ValueError, 'Document run failed'):
            collect(self.root)
        today = tomllib.loads(self.path.read_text())['updated']
        self.write(f'log/{today}.mdx', '# Failure\n\nRun `failed` stopped on readiness. No strength conclusion.\n')
        self.update(logs=[f'log/{today}.mdx'])
        self.assertEqual(collect(self.root)[0]['runs'], ['failed'])
        self.write('records/runs/orphan.md', '# Run\n\nExperiment: `missing`.\n')
        with self.assertRaisesRegex(ValueError, 'no filed experiment'):
            collect(self.root)

    def test_reports_require_dates_an_owner_and_existing_references(self):
        self.write('reports/result.mdx', '# Undated result\n')
        with self.assertRaisesRegex(ValueError, 'Unfiled report'):
            collect(self.root)
        self.update(reports=['reports/result.mdx'])
        with self.assertRaisesRegex(ValueError, 'quoted date'):
            collect(self.root)
        self.write('reports/result.mdx', '---\ndate: "2026-09-08"\n---\n# Result\n')
        collect(self.root)
        self.update(reports=['reports/missing.mdx'])
        with self.assertRaisesRegex(ValueError, 'Missing or invalid'):
            collect(self.root)
        self.update(reports=['reports/../private.md'])
        with self.assertRaisesRegex(ValueError, 'Expected a document'):
            collect(self.root)

    def test_metadata_does_not_become_mdx_or_break_a_table(self):
        self.update(title='<script>{1 + 1}</script> | [link]', outcome='A\nnew paragraph')
        sync(self.root)
        source = (self.root / 'log/experiments.mdx').read_text()
        self.assertNotIn('<script>', source)
        self.assertNotIn('{1 + 1}', source)
        self.assertIn('&#124;', source)
        self.assertIn('A new paragraph', source)
        self.assertEqual(cell('plain text'), 'plain text')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, text=True)

    def initialize_git(self):
        self.write('.gitignore', '/.worktrees/\n')
        self.git('init', '-q', '-b', 'main')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture')

    def test_nested_worktrees_resolve_the_canonical_research_and_server_location(self):
        self.initialize_git()
        first = worktree(self.root, 'first')
        second = worktree(first, 'second')
        self.assertEqual(first, self.root / '.worktrees/first')
        self.assertEqual(second, self.root / '.worktrees/second')
        self.assertEqual(canonical_root(second), self.root)
        self.assertEqual(canonical_root(second).parent / 'server', self.root.parent / 'server')

    def test_worktree_does_not_silently_drop_dirty_source(self):
        self.initialize_git()
        self.write('unintegrated.txt', 'Important source change')
        with self.assertRaisesRegex(ValueError, 'omit them'):
            worktree(self.root, 'candidate')
        self.assertFalse((self.root / '.worktrees/candidate').exists())


if __name__ == '__main__':
    unittest.main()
