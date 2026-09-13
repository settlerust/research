#!/usr/bin/env python3
"""Seating-corrected effects, decision cost, and trade diagnostics for the
search/settings-tables swapped pairs.

Each arm is two engine runs on the same seeds: half A seats the candidate in
slot 0, half B seats it in slot 1. Per seed, the seating-corrected effect is
half the difference of the two slot-0-minus-slot-1 contrasts and the seating
term half their sum, each with a normal-approximation 95 percent interval over
seeds. The script locates the completed run of a registered half from its
experiment UUID, so it works in the worktree where the runs happened and in
the canonical checkout after the runs are archived.

Usage:

    python3 analysis/settings_tables.py            # every arm, every stage
    python3 analysis/settings_tables.py scenarios4 scenarios16
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

T = 'v2:{"depth":2,"leaf":{"tables":"/home/keshav/settlers/research/artifacts/ntuple/hex-portfolio-main.bin"}}'

# arm -> {stage: (half A experiment, half B experiment)}
PAIRS = {
    'scenarios4': {
        'development': ('d6cbff3d-7e92-4f47-bbc9-97da3c2532a9', '33654a28-86e9-4026-93e2-111b34913669'),
        'confirmation': ('dcfd9ca5-170f-43a7-a1f0-36117e7c7990', 'ee1751fb-ec20-4df1-b402-6d97a405bd0d'),
    },
    'scenarios16': {
        'development': ('767a4f08-e4d9-48da-83bb-d2e952feaf69', 'f650a242-2e6a-4075-a80d-da4ee753441a'),
        'confirmation': ('ed82c2ee-5197-4e70-a3e6-ae4a20d64a33', 'e5b13479-5578-4810-bd6f-da6b3fb779fb'),
    },
    'samples1': {
        'development': ('f959a49e-5745-4623-9bb9-e0a43f9ea964', 'e4f5ae29-919c-4bd4-83ae-98812ea00bc3'),
        'confirmation': ('142fdc9a-e4be-4418-9008-5b942dc78daf', 'bfb9bed6-58cd-48c5-aa91-2b029b5c0f9a'),
    },
    'samples8': {
        'development': ('97bd74e0-164b-4d79-bcab-390edc31c129', 'adf4e1c3-f93f-4f7e-9631-bd595a2beb2a'),
        'confirmation': ('449ea466-728b-45e0-a177-9c220e3e8415', '13a7cf69-526c-4f94-b434-0ee56051a5f8'),
        'population': ('82ff6f24-174a-4d2b-babf-fa1a95619589', '75b81db1-c6e6-483b-aafc-8ad707ecc0f4'),
        'extension-l1': ('12b83328-8fd5-402f-aa7e-08c8dc8b38fd', 'fbd6fe9d-3771-4e25-bc1f-bf2fb38625bd'),
        'extension-l2': ('d5cb3195-5a58-460a-bee7-ee62fe907d63', 'b16d5306-09ee-4af4-a7fe-e34494197bf0'),
    },
    'inner_scenarios2': {
        'development': ('e071b629-8043-4eff-8fb0-ac694cac0f78', 'f364cf12-1945-4653-9fe3-8bfa92fe5f38'),
        'confirmation': ('25ed5f85-6ab3-4949-80d0-b3bce5237971', 'e2445b6e-c49c-4396-85f6-9052f8921028'),
    },
    'leaf_opponents': {
        'development': ('a20b6abd-d8b6-4f66-b634-5df40495953e', 'face5b0d-d070-4e83-91df-d6fb6ae5ee4b'),
        'confirmation': ('a5e38bc5-ff5d-4365-bdee-f89379bf64b6', 'b3c000ac-fec6-48ba-87e0-1cec1c89ba34'),
        'population': ('9aef447a-d703-454a-8970-92d463017015', 'bddfe32b-940f-4ea0-833f-2c0db3274a3c'),
        'extension-l1': ('e222c91f-2724-4730-8f81-9a1198ca4e1f', 'd46a4f48-401e-49fb-8a93-0dc5b4adeca1'),
        'extension-l2': ('36817410-f3b0-4dd3-a61f-70bc9676bc06', '4d02ea83-f6e1-4e4b-afd1-24ab954ffcb6'),
    },
    'counts_only': {
        'development': ('ef501bc5-7196-4ad6-a939-09f00414d771', 'b3795b5e-aa62-40be-ad6c-53d075512ecb'),
        'confirmation': ('1667548f-63ed-4d58-bff0-a1477e978867', 'dfbd6b4c-1438-44e9-b69b-313d048f6fcf'),
        'population': ('d4778a73-5587-441c-8cbf-82a53f87d096', '4efbf0e1-bea3-407f-8f8a-078f649805eb'),
    },
    'propose_false': {
        'development': ('e53c45bd-a7ee-4ef8-8772-3780c1cfef31', '1172dcee-95da-44af-a86c-9f5ee0d12fbf'),
        'confirmation': ('87550a5a-5149-418b-a056-aa6d0a8372a9', 'a567b9c2-92a1-49b5-b7ef-c623fd51a197'),
        'population': ('3c661aad-8bcf-48cd-988b-0cbf3c50209d', '001e2f3b-f70e-41b0-b061-247eeb855557'),
    },
    'reciprocity': {
        'development': ('95aac00b-f396-4a5c-b023-db360692802b', '495e1a17-5a74-438e-b660-06219ca881c7'),
        'confirmation': ('ca442984-d942-4e50-b036-e76b85372074', 'de3228ec-9440-4ac1-ac6d-81c2d99976e5'),
        'population': ('4e7a760b-0fa1-4e5e-8269-aee7f6030105', '5b23ab6d-1cbc-4e77-82e2-5c281248e7d0'),
    },
}

STAGE_SEEDS = {'development': '0-63', 'confirmation': '800-863', 'population': '800-863',
               'extension-l1': '864-927', 'extension-l2': '864-927'}
LINEUP = {'development': 'L1', 'confirmation': 'L1', 'population': 'L2',
          'extension-l1': 'L1', 'extension-l2': 'L2'}
DIAG_KEYS = ['player_trades', 'offers', 'offers_accepted', 'development_bought', 'cities_built',
             'settlements_built', 'roads_built', 'cards_discarded', 'bank_trades', 'times_robbed']
SEAT_KEYS = ['counters', 'counters_accepted', 'declined', 'accepted_others']


def completed_run(experiment):
    """The one completed run of an experiment, or None."""
    found = []
    for manifest in (ROOT / 'runs').glob('*/manifest.json'):
        data = json.loads(manifest.read_text())
        if data.get('experiment') != experiment:
            continue
        summary = manifest.parent / 'summary.json'
        if summary.is_file() and json.loads(summary.read_text()).get('status') == 'completed':
            found.append((data['created_at'], manifest.parent))
    if not found:
        return None
    if len(found) > 1:
        raise SystemExit(f'experiment {experiment} has {len(found)} completed runs')
    return sorted(found)[-1][1]


def per_seed_diffs(folder):
    rows = [json.loads(line) for line in (folder / 'games.jsonl').read_text().splitlines() if line.strip()]
    by_seed = {}
    for r in rows:
        if r['game']['status'] != 'completed':
            continue
        w = by_seed.setdefault(r['seed'], [0, 0, 0])
        w[2] += 1
        if r['winner_slot'] == 0:
            w[0] += 1
        elif r['winner_slot'] == 1:
            w[1] += 1
    return {s: (w0 - w1) / n for s, (w0, w1, n) in by_seed.items()}


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def pair_of(arm, stage):
    a_exp, b_exp = PAIRS[arm][stage]
    a, b = completed_run(a_exp), completed_run(b_exp)
    if not a or not b:
        return None
    da, db = per_seed_diffs(a), per_seed_diffs(b)
    if set(da) != set(db):
        raise SystemExit(f'{arm}/{stage}: halves did not play the same seeds')
    effects = [(da[s] - db[s]) / 2 for s in sorted(da)]
    seating = [(da[s] + db[s]) / 2 for s in sorted(da)]
    eff, lo, hi = interval(effects)
    seat, slo, shi = interval(seating)
    summary_a = json.loads((a / 'summary.json').read_text())
    summary_b = json.loads((b / 'summary.json').read_text())
    def slot_stats(summary, cand_slot, ctrl_slot):
        cand = next(r for r in summary['slots'] if r['slot'] == cand_slot)
        ctrl = next(r for r in summary['slots'] if r['slot'] == ctrl_slot)
        return {'cand': cand, 'ctrl': ctrl}
    stats_a = slot_stats(summary_a, 0, 1)  # candidate slot 0
    stats_b = slot_stats(summary_b, 1, 0)  # candidate slot 1
    diag = {}
    for key in DIAG_KEYS:
        diag[key] = {
            'cand': (stats_a['cand']['builds'][key] + stats_b['cand']['builds'][key]) / 2,
            'ctrl': (stats_a['ctrl']['builds'][key] + stats_b['ctrl']['builds'][key]) / 2,
        }
    # counters and declines are per-seat fields of the raw records, not summary builds
    def seat_mean(folder, slot):
        sums, n = {}, 0
        for line in (folder / 'games.jsonl').read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r['game']['status'] != 'completed':
                continue
            s = r['game']['seats'][r['slots'].index(slot)]
            for key in SEAT_KEYS:
                sums[key] = sums.get(key, 0) + s.get(key, 0)
            n += 1
        return {key: v / n for key, v in sums.items()} if n else {}
    ma_a, ma_b = seat_mean(a, 0), seat_mean(b, 1)
    mc_a, mc_b = seat_mean(a, 1), seat_mean(b, 0)
    for key in SEAT_KEYS:
        diag[key] = {
            'cand': (ma_a.get(key, 0) + ma_b.get(key, 0)) / 2,
            'ctrl': (mc_a.get(key, 0) + mc_b.get(key, 0)) / 2,
        }
    return {
        'arm': arm, 'stage': stage, 'seeds': len(effects), 'lineup': LINEUP[stage],
        'effect': eff, 'effect_lo': lo, 'effect_hi': hi,
        'seating': seat, 'seating_lo': slo, 'seating_hi': shi,
        'runs': {'a': a.name, 'b': b.name},
        'experiments': {'a': a_exp, 'b': b_exp},
        'decision_ms': {'cand': (stats_a['cand']['mean_decision_ms'] + stats_b['cand']['mean_decision_ms']) / 2,
                        'ctrl': (stats_a['ctrl']['mean_decision_ms'] + stats_b['ctrl']['mean_decision_ms']) / 2},
        'wins': {'a_cand': stats_a['cand']['wins'], 'a_ctrl': stats_a['ctrl']['wins'],
                 'b_cand': stats_b['cand']['wins'], 'b_ctrl': stats_b['ctrl']['wins']},
        'points': {'cand': (stats_a['cand']['mean_points'] + stats_b['cand']['mean_points']) / 2,
                   'ctrl': (stats_a['ctrl']['mean_points'] + stats_b['ctrl']['mean_points']) / 2},
        'diagnostics': diag,
    }


def pooled(arm, stages):
    """After-the-fact pooling of per-seed effects over stages."""
    values = []
    for stage in stages:
        a_exp, b_exp = PAIRS[arm][stage]
        a, b = completed_run(a_exp), completed_run(b_exp)
        if not a or not b:
            return None
        da, db = per_seed_diffs(a), per_seed_diffs(b)
        values += [(da[s] - db[s]) / 2 for s in sorted(da)]
    mean, lo, hi = interval(values)
    return {'seeds': len(values), 'effect': mean, 'effect_lo': lo, 'effect_hi': hi}


def main():
    arms = sys.argv[1:] or list(PAIRS)
    results = {}
    for arm in arms:
        for stage in PAIRS[arm]:
            r = pair_of(arm, stage)
            if not r:
                print(f'{arm} {stage}: runs not complete yet')
                continue
            results.setdefault(arm, {})[stage] = r
            print(f"{arm} {stage} ({r['lineup']}, seeds {r['seeds']}): "
                  f"effect {r['effect']:+.3f} ({r['effect_lo']:+.3f} to {r['effect_hi']:+.3f}), "
                  f"seating {r['seating']:+.3f} ({r['seating_lo']:+.3f} to {r['seating_hi']:+.3f}); "
                  f"candidate {r['decision_ms']['cand']:.0f} ms vs control {r['decision_ms']['ctrl']:.0f} ms; "
                  f"runs {r['runs']['a']}, {r['runs']['b']}")
        stages = [s for s in ('development', 'confirmation') if s in results.get(arm, {})]
        if len(stages) == 2:
            p = pooled(arm, stages)
            print(f'{arm} pooled L1 ({p["seeds"]} seeds): effect {p["effect"]:+.3f} '
                  f'({p["effect_lo"]:+.3f} to {p["effect_hi"]:+.3f}) [after-the-fact pooling]')
        ext = [s for s in ('development', 'confirmation', 'extension-l1') if s in results.get(arm, {})]
        if len(ext) == 3:
            p = pooled(arm, ext)
            print(f'{arm} pooled L1 with extension ({p["seeds"]} seeds): effect {p["effect"]:+.3f} '
                  f'({p["effect_lo"]:+.3f} to {p["effect_hi"]:+.3f}) [after-the-fact pooling]')
        l2 = [s for s in ('population', 'extension-l2') if s in results.get(arm, {})]
        if len(l2) == 2:
            p = pooled(arm, l2)
            print(f'{arm} pooled L2 ({p["seeds"]} seeds): effect {p["effect"]:+.3f} '
                  f'({p["effect_lo"]:+.3f} to {p["effect_hi"]:+.3f}) [after-the-fact pooling]')
    (ROOT / 'analysis' / 'settings_tables.json').write_text(json.dumps(results, indent=1))
    print('wrote analysis/settings_tables.json')


if __name__ == '__main__':
    main()
