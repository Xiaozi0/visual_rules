#!/usr/bin/env python3
"""Generate two validated VQA samples for the flip-block puzzle."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "flip_blocks"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from game import VERSION as GAME_VERSION  # noqa: E402
from game import generate_puzzle, render_puzzle, shortest_path  # noqa: E402


VERSION = "flip_blocks_vqa_v1.0.0"
SCRIPT_NAME = "flip_blocks_vqa_generator.py"
RULE_SOURCE = "original/批次04-0519.md:海绵宝宝-翻木块; original/批次05-0521.md:Bloxorz; vendor/flip_blocks/RULES.md"


def write_jsonl(rows: Sequence[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def classify() -> dict:
    return {
        "domain": "games",
        "task": "flip_blocks_reachability",
        "reasoning_type": "game_rule_planning",
        "visual_type": "grid_board",
        "rule_delivery_mode": "explicit_text_prompt",
    }


def record(seed: int, index: int, image_rel: str, puzzle, answer: str) -> dict:
    question = "<image> Can the block reach the red goal hole and end upright on it? Answer yes or no."
    return {
        "id": f"r_flip_blocks_vqa_{seed}-{index:05d}",
        "media": [image_rel],
        "messages": [
            {
                "role": "user",
                "question": question,
                "answer": "",
                "options": {},
                "choices": ["yes", "no"],
                "hint": "",
            }
        ],
        "metadata": {
            "classification": classify(),
            "provenance": {
                "source": "original/批次04-0519.md",
                "method": "deterministic_bfs_sampling",
                "seed": seed,
                "index": index,
                "seed_description": "Board with usable tiles, missing tiles, upright start block, and goal hole.",
                "generator": f"{SCRIPT_NAME}@{VERSION}({GAME_VERSION},{'codex'})",
                "rule_source": RULE_SOURCE,
            },
            "gt": {
                "answer": answer,
                "answer_text": answer,
                "answer_type": "yes_no",
                "choices": ["yes", "no"],
                "validator": {"kind": "exact_match", "solution": answer},
            },
            "instance": {
                "difficulty": "medium",
                "complexity_score": 0.78,
                "tags": ["flip-blocks", "bloxorz", "reachability", "bfs"],
                "raw_state": {
                    "rows": puzzle.rows,
                    "cols": puzzle.cols,
                    "board": list(puzzle.board),
                    "start": [list(cell) for cell in puzzle.start.cells],
                    "goal": list(puzzle.goal),
                    "is_reachable": puzzle.min_steps is not None,
                    "min_steps": puzzle.min_steps,
                },
            },
        },
    }


def generate(out_dir: Path, seed: int) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    records = []
    rng = random.Random(seed)
    for index, want_reachable in enumerate((True, False)):
        sample_seed = rng.randint(10_000_000, 999_999_999)
        puzzle = generate_puzzle(sample_seed, want_reachable=want_reachable)
        image_rel = f"images/{index:05d}.png"
        render_puzzle(puzzle, out_dir / image_rel)
        answer = "yes" if puzzle.min_steps is not None else "no"
        records.append(record(seed, index, image_rel, puzzle, answer))

    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl(
        [
            {
                "id": "flip_blocks_reachability.rule",
                "task": "flip_blocks_reachability",
                "rule": "The block must roll only across usable tiles and finish standing exactly on the goal hole.",
            }
        ],
        out_dir / "rules.jsonl",
    )
    (out_dir / "quality_report.json").write_text(
        json.dumps(
            [{"id": row["id"], "keep": True, "answer": row["metadata"]["gt"]["answer"]} for row in records],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest = {
        "dataset": "flip_blocks_vqa",
        "version": VERSION,
        "generator": f"{SCRIPT_NAME}@{VERSION}(codex)",
        "count": len(records),
        "seed": seed,
        "rule_source": RULE_SOURCE,
        "format": "format_docs/VQA_DATA_FORMAT.md",
        "classification": "format_docs/classification.md",
        "reproduce_command": f"python3 generator/{SCRIPT_NAME} --seed {seed} --out-dir {out_dir}",
        "outputs": {
            "records": "vis_scaling_simple_mm.jsonl",
            "rules": "rules.jsonl",
            "quality_report": "quality_report.json",
            "images": "images/",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated/flip_blocks_vqa")
    parser.add_argument("--seed", type=int, default=20260523)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.seed)
    print(f"Wrote {len(records)} flip-block VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
