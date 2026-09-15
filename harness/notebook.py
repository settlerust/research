"""File investigations, link immutable evidence, and refresh the public notebook."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SLUG = r'[a-z0-9]+(?:-[a-z0-9]+)*'
START = '[research-studies:start]: #'
END = '[research-studies:end]: #'
STATES = {'proposed', 'active', 'blocked', 'complete'}


def canonical_root(root):
    """Linked worktrees share the canonical checkout's Git directory."""
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                            capture_output=True, text=True, check=True)
    return Path(result.stdout.strip()).parent


def study_path(root, identifier):
    if not re.fullmatch(f'{SLUG}/{SLUG}', identifier):
        raise ValueError('Study ID must be APPROACH/SLUG or log/SLUG')
    owner, slug = identifier.split('/')
    folder = root / 'log' if owner == 'log' else root / 'approaches' / owner
    if owner != 'log' and not (folder / 'README.mdx').is_file():
        raise ValueError(f'Unknown approach: {owner}; create its study brief first')
    return folder / 'studies' / f'{slug}.toml'


def require_study(root, identifier):
    path = study_path(root, identifier)
    if not path.is_file():
        raise ValueError(f'Unknown study {identifier}; use just study {identifier} --title ... --question ...')
    data = tomllib.loads(path.read_text())
    if data['status'] == 'complete':
        raise ValueError(f'Study {identifier} is complete; create a follow-up study for new evidence')
    return path


def new_study(root, identifier, title, question):
    path = study_path(root, identifier)
    if not title.strip() or not question.strip():
        raise ValueError('A study needs a title and a research question')
    today = date.today().isoformat()
    fields = dict(id=identifier, title=title, created=today, updated=today, status='proposed',
                  question=question, outcome='No experiment has been executed.',
                  next_step='Register a fixed candidate, comparison, budget, and decision rule.',
                  attribution='unknown', reports=[], logs=[], legacy_experiments=[])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as target:
        target.write(''.join(f'{key} = {json.dumps(value, ensure_ascii=False)}\n' for key, value in fields.items()))
    return path


def document(root, name, prefix):
    if not isinstance(name, str) or not name.startswith(prefix + '/') or '..' in Path(name).parts:
        raise ValueError(f'Expected a document under {prefix}/: {name}')
    path = root / name
    if path.suffix not in ('.md', '.mdx') or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Missing or invalid document: {name}')
    return path.read_text()


def load_studies(root):
    studies = {}
    paths = sorted((root / 'approaches').glob('*/studies/*.toml')) + sorted((root / 'log/studies').glob('*.toml'))
    for path in paths:
        data = tomllib.loads(path.read_text())
        for key in ['id', 'title', 'created', 'updated', 'status', 'question', 'outcome', 'next_step', 'attribution']:
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f'{path.relative_to(root)} needs {key}')
        if study_path(root, data['id']) != path or data['id'] in studies:
            raise ValueError(f'Duplicate or misplaced study: {data["id"]}')
        if data['status'] not in STATES:
            raise ValueError(f'Unknown study status: {data["status"]}')
        for key in ['created', 'updated']:
            if date.fromisoformat(data[key]).isoformat() != data[key]:
                raise ValueError(f'Use YYYY-MM-DD for {key}')
        if data['updated'] < data['created']:
            raise ValueError(f'Study update predates creation: {data["id"]}')
        for key in ['reports', 'logs', 'legacy_experiments']:
            if not isinstance(data.get(key), list) or any(not isinstance(v, str) for v in data[key]):
                raise ValueError(f'{data["id"]} needs a {key} array')
            if len(set(data[key])) != len(data[key]):
                raise ValueError(f'Duplicate {key} in {data["id"]}')
        texts = []
        for name in data['reports']:
            text = document(root, name, 'reports')
            match = re.search(r'^date: "(\d{4}-\d{2}-\d{2})"$', text, re.M)
            if not match or date.fromisoformat(match[1]).isoformat() != match[1]:
                raise ValueError(f'Report needs a quoted date: {name}')
            texts.append(text)
        for name in data['logs']:
            if not re.fullmatch(r'log/\d{4}-\d{2}-\d{2}\.mdx', name):
                raise ValueError(f'Use a dated daily log: {name}')
            if Path(name).stem > data['updated']:
                raise ValueError(f'Update the study date after adding {name}')
            texts.append(document(root, name, 'log'))
        if data['status'] == 'complete' and not data['logs']:
            raise ValueError(f'Completed study needs a dated interpretation: {data["id"]}')
        data['evidence_text'] = '\n'.join(texts)
        data['experiments'] = []
        data['runs'] = []
        studies[data['id']] = data
    return studies


def collect(root):
    studies = load_studies(root)
    legacy = {}
    for identifier, study in studies.items():
        for experiment in study['legacy_experiments']:
            if experiment in legacy:
                raise ValueError(f'Experiment belongs to two studies: {experiment}')
            legacy[experiment] = identifier
    protocols = {}
    for path in sorted((root / 'experiments').glob('*.toml')):
        data = tomllib.loads(path.read_text())
        if data.get('id') != path.stem:
            raise ValueError(f'Experiment ID and filename disagree: {path.name}')
        if 'study' in data and path.stem in legacy:
            raise ValueError(f'Use either registered ownership or legacy mapping: {path.stem}')
        owner = data.get('study', legacy.get(path.stem))
        if owner not in studies:
            raise ValueError(f'Unfiled experiment {path.stem}; register with --study or file its immutable legacy ID')
        protocols[path.stem] = owner
        studies[owner]['experiments'].append(path.stem)
    if missing := legacy.keys() - protocols.keys():
        raise ValueError(f'Missing legacy experiments: {sorted(missing)}')
    for path in sorted((root / 'records/runs').glob('*.md')):
        match = re.search(r'Experiment: `([^`]+)`', path.read_text())
        if not match or match[1] not in protocols:
            raise ValueError(f'Run record has no filed experiment: {path.name}')
        study = studies[protocols[match[1]]]
        study['runs'].append(path.stem)
        if not study['logs'] or path.stem not in study['evidence_text']:
            raise ValueError(f'Document run {path.stem}, including failures, in {study["id"]} reports/logs')
    owned = [name for study in studies.values() for name in study['reports']]
    if len(owned) != len(set(owned)):
        raise ValueError('A report must have exactly one owning study; cross-link related studies')
    for path in sorted((root / 'reports').glob('*')):
        if path.suffix in ('.md', '.mdx') and path.relative_to(root).as_posix() not in owned:
            raise ValueError(f'Unfiled report: {path.name}; add it to its study reports array')
    return sorted(studies.values(), key=lambda study: (study['created'], study['id']))


def cell(value):
    # Study metadata is plain text, never a second MDX/template language.
    for old, new in [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'), ('{', '&#123;'), ('}', '&#125;'),
                     ('|', '&#124;'), ('[', '&#91;'), (']', '&#93;'), ('*', '&#42;'), ('`', '&#96;')]:
        value = value.replace(old, new)
    return ' '.join(value.split())


def href(name):
    return '/research/' + re.sub(r'\.mdx?$', '', name).removesuffix('/README')


def render(studies):
    run_ids = [identifier for study in studies for identifier in study['runs']]
    def evidence(value):
        def replace(match):
            found = [identifier for identifier in run_ids if identifier.startswith(match[0])]
            return f'[run record](/research/records/runs/{found[0]})' if len(found) == 1 else match[0]
        return re.sub(r'\b[a-f0-9]{8}(?:-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})?\b', replace, cell(value))
    lines = ['| Updated | Investigation | Status | Finding and next step |' , '| --- | --- | --- | --- |']
    for study in sorted(studies, key=lambda item: (item["updated"], item["id"]), reverse=True):
        owner = study['id'].split('/')[0]
        destination = href(study['reports'][0]) if study['reports'] else (
            f'/research/approaches/{owner}' if owner != 'log' else '/research/docs/experiment-program')
        sources = [f'[{cell(Path(name).stem.replace("-", " ").capitalize())}]({href(name)})'
                   for name in study['reports'][1:]]
        sources += [f'[Log {Path(name).stem}]({href(name)})' for name in study['logs']]
        lines.append(f'| {study["updated"]} | [{cell(study["title"])}]({destination}) | {study["status"].capitalize()} | '
                     f'{evidence(study["outcome"])} Next: {evidence(study["next_step"])} {" · ".join(sources)} |')
    return '\n'.join(lines) + '\n'


def replace_section(source, content):
    section = f'{START}\n\n## Tracked investigations\n\n<AgentContext title="Study findings and next steps">\n\n{content}\n</AgentContext>\n\n{END}'
    if START not in source and END not in source:
        return source.rstrip() + '\n\n' + section + '\n'
    if source.count(START) != 1 or source.count(END) != 1 or source.index(START) > source.index(END):
        raise ValueError('Malformed generated study section')
    before, rest = source.split(START)
    _, after = rest.split(END)
    return before + section + after


def sync(root, check=False):
    studies = collect(root)
    outputs = {}
    index = ('---\ntitle: Experiments\nsummary: Every published experiment, newest first, with recorded results and links to the full evidence.\n---\n\n'
             '# Experiments\n\n'
             'Browse the findings, compare the recorded results, and open a report for its full experiment. '
             'Green intervals sit above zero, red below; gray intervals leave the direction unresolved.\n\n'
             '<ExperimentTimeline />\n\n'
             '<AgentContext title="All study records and next steps">\n\n'
             'The ledger also includes proposed studies, ongoing work, failures, and supporting reports.\n\n'
             + render(studies) + '\n</AgentContext>\n')
    outputs[root / 'log/experiments.mdx'] = index
    for path in [root / 'docs/roadmap.md', *sorted((root / 'approaches').glob('*/README.mdx'))]:
        selected = studies if path.name == 'roadmap.md' else [s for s in studies if s['id'].split('/')[0] == path.parent.name]
        source = path.read_text()
        if selected or START in source:
            outputs[path] = replace_section(source, render(selected))
    changed = [path for path, text in outputs.items() if not path.exists() or path.read_text() != text]
    if check and changed:
        raise ValueError('Notebook is stale; run just notebook: ' + ', '.join(str(p.relative_to(root)) for p in changed))
    for path in changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[path])
    return studies, changed


def worktree(root, name):
    if not re.fullmatch(SLUG, name):
        raise ValueError('Use a lowercase hyphenated worktree name')
    canonical = canonical_root(root)
    dirty = subprocess.run(['git', '-C', str(root), 'status', '--porcelain'], capture_output=True, text=True, check=True)
    if dirty.stdout.strip():
        raise ValueError('Integrate or commit the current changes before creating a worktree; Git would omit them')
    destination = canonical / '.worktrees' / name
    destination.parent.mkdir(exist_ok=True)
    subprocess.run(['git', '-C', str(root), 'worktree', 'add', '-b', f'research/{name}', str(destination), 'HEAD'], check=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['sync', 'check', 'site-check']:
        commands.add_parser(name)
    study = commands.add_parser('study')
    study.add_argument('id')
    study.add_argument('--title', required=True)
    study.add_argument('--question', required=True)
    tree = commands.add_parser('worktree')
    tree.add_argument('name')
    args = parser.parse_args()
    try:
        if args.command == 'study':
            print(new_study(ROOT, args.id, args.title, args.question))
        elif args.command == 'worktree':
            print(worktree(ROOT, args.name))
        else:
            studies, changed = sync(ROOT, check=args.command != 'sync')
            print(f'Notebook: {len(studies)} studies, {sum(len(s["experiments"]) for s in studies)} protocols, '
                  f'{sum(len(s["runs"]) for s in studies)} run records; {len(changed)} pages refreshed.')
            if args.command == 'site-check':
                web = canonical_root(ROOT).parent / 'web'
                subprocess.run(['npm', 'run', 'check:research'], cwd=web, check=True,
                               env=os.environ | {'SETTLERS_RESEARCH_DIR': str(ROOT)})
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
