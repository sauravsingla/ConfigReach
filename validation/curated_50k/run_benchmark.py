from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from configreach.engine import scan


def metrics(c: Counter[str]) -> dict[str, float | int]:
    tp, fp, tn, fn = c['tp'], c['fp'], c['tn'], c['fn']
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn)
    return {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn, 'precision': precision, 'recall': recall, 'f1': f1, 'accuracy': accuracy}


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument('--dataset', type=Path, default=root / 'data' / 'configreach_50k_scenarios.jsonl')
    parser.add_argument('--results-json', type=Path, default=root / 'results' / 'configreach_50k_runtime.json')
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != 50000:
        raise SystemExit(f'expected 50,000 rows, found {len(rows):,}')

    overall: Counter[str] = Counter()
    by_group: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)

    with tempfile.TemporaryDirectory(prefix='configreach-50k-') as tmp:
        corpus = Path(tmp)
        for row in rows:
            case_dir = corpus / row['scenario_id']
            case_dir.mkdir()
            (case_dir / row['suggested_filename']).write_text(row['snippet'], encoding='utf-8')

        report = scan(corpus, use_cache=False)
        detected = set(report.keys)
        for row in rows:
            expected = bool(row['expected_detect'])
            predicted = row['expected_key'] in detected
            outcome = 'tp' if expected and predicted else 'fn' if expected else 'fp' if predicted else 'tn'
            overall[outcome] += 1
            by_group[row['group']][outcome] += 1
            by_variant[f"{row['group']}::{row['variant']}"][outcome] += 1

    result = {
        'benchmark': 'ConfigReach Curated 50K Benchmark',
        'scenario_count': len(rows),
        'dataset_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        'method': 'configreach.engine.scan over materialized isolated scenarios',
        'qualification': 'Benchmark-specific controlled result; not a claim of universal real-world accuracy.',
        'overall': metrics(overall),
        'by_group': {group: metrics(counts) for group, counts in sorted(by_group.items())},
        'by_variant': {variant: metrics(counts) for variant, counts in sorted(by_variant.items())},
    }
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result['overall'], indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
