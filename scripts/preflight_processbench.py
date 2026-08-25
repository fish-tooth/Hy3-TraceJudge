"""ProcessBench dataset preflight (P1-T04 / EXT-02).

Loads the real ProcessBench dataset and prints the ground truth about its schema,
label semantics, index base, split names, and sample counts. This must be reviewed
BEFORE the evaluator is finalized, so we never rely on assumed schema.

Usage:
    python scripts/preflight_processbench.py [--max-print N]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset

DATASET = "Qwen/ProcessBench"
SAMPLE_SIZE = 20
SEED = 42


def _fmt(v) -> str:
    s = repr(v)
    return s if len(s) <= 200 else s[:200] + "..."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-print", type=int, default=5)
    parser.add_argument("--out", type=str, default="reports/preflight_processbench.md")
    args = parser.parse_args()

    lines: list[str] = []
    lines.append("# ProcessBench Preflight Report\n")

    try:
        configs = get_dataset_config_names(DATASET)
    except Exception as exc:  # noqa: BLE001
        configs = None
        lines.append(f"- ERROR getting configs: {exc}\n")

    lines.append(f"- dataset: {DATASET}")
    lines.append(f"- configs: {configs}\n")

    if not configs:
        print("\n".join(lines))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("\n".join(lines), encoding="utf-8")
        print(f"[preflight] configs unavailable; wrote {args.out}")
        return 1

    all_info: dict = {}
    for cfg in configs:
        try:
            ds = load_dataset(DATASET, cfg)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"\n## config={cfg}\n- ERROR loading: {exc}\n")
            continue

        lines.append(f"\n## config={cfg}\n")
        if hasattr(ds, "keys"):
            lines.append(f"- splits: {list(ds.keys())}")
            for split, d in ds.items():
                lines.append(f"  - {split}: {len(d)} rows")
        else:
            lines.append(f"- rows: {len(ds)}")

        # Pick a representative split for schema inspection.
        if hasattr(ds, "keys"):
            target = next(iter(ds.values()))
        else:
            target = ds

        lines.append(f"- columns: {target.column_names}")
        lines.append(f"- features: {json.dumps(target.features, default=str)[:600]}\n")

        # Inspect label semantics.
        label_vals = []
        final_correct_vals = []
        step_lens = []
        if "label" in target.column_names:
            for row in target:
                label_vals.append(row["label"])
            label_vals = label_vals  # noqa: PLW2901 (kept for readability)
            lines.append(f"- label min/max: {min(label_vals)} / {max(label_vals)}")
            lines.append(f"- label distribution: {dict(Counter(label_vals))}\n")

        # Inspect steps and final_answer_correct.
        if "steps" in target.column_names:
            for row in target:
                step_lens.append(len(row["steps"]))
            lines.append(f"- steps length min/max/mean: {min(step_lens)} / {max(step_lens)}"
                         f" / {sum(step_lens) / max(1, len(step_lens)):.2f}\n")

        if "final_answer_correct" in target.column_names:
            for row in target:
                final_correct_vals.append(row["final_answer_correct"])
            lines.append(
                f"- final_answer_correct distribution: {dict(Counter(final_correct_vals))}\n"
            )

        # Print a few raw examples.
        lines.append(f"### first {args.max_print} raw examples (config={cfg})")
        for i, row in enumerate(target):
            if i >= args.max_print:
                break
            lines.append(f"  - id={_fmt(row.get('id'))}")
            lines.append(f"    problem={_fmt(row.get('problem'))}")
            lines.append(f"    steps={_fmt(row.get('steps'))}")
            lines.append(f"    label={row.get('label')}")
            lines.append(f"    final_answer_correct={row.get('final_answer_correct')}")
            lines.append(f"    source={row.get('source')}")

        all_info[cfg] = {
            "columns": target.column_names,
            "label_min": min(label_vals) if label_vals else None,
            "label_max": max(label_vals) if label_vals else None,
            "label_dist": dict(Counter(label_vals)),
        }

    # Stratified 20-sample list for manual review.
    lines.append(f"\n## manual review sample (n={SAMPLE_SIZE}, seed={SEED})")
    if configs:
        cfg = configs[0]
        try:
            ds = load_dataset(DATASET, cfg)
            target = next(iter(ds.values())) if hasattr(ds, "keys") else ds
            rows = list(target)
            rng = random.Random(SEED)
            sample = rng.sample(rows, min(SAMPLE_SIZE, len(rows)))
            lines.append("| id | label | final_answer_correct | source |")
            lines.append("|---|---|---|---|")
            for r in sample:
                lines.append(f"| {r.get('id')} | {r.get('label')} | "
                             f"{r.get('final_answer_correct')} | {r.get('source')} |")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"- ERROR sampling: {exc}")

    report = "\n".join(lines)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[preflight] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
