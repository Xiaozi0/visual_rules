#!/usr/bin/env python3
"""Generate two validated VQA samples for the SpongeBob cube-roll puzzle."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "haimian_flip"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from game import VERSION as GAME_VERSION  # noqa: E402
from game import generate_puzzle, puzzle_to_dict, render_puzzle  # noqa: E402


VERSION = "haimian_flip_vqa_v1.0.0"
SCRIPT_NAME = "haimian_flip_vqa_generator.py"
RULE_SOURCE = "original/批次04-0519.md:海绵宝宝-翻木块; original/haimian_gemini; vendor/haimian_flip/RULES.md"
GENERATOR_TAG = "codex"


def write_jsonl(rows: Sequence[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def classification() -> dict:
    return {
        "domain": "games",
        "task": "spongebob_cube_orientation",
        "reasoning_type": "spatial",
        "visual_type": "grid_board",
        "rule_delivery_mode": "explicit_text_prompt",
    }


def build_question() -> str:
    return (
        "<image> A SpongeBob cube starts in the shown orientation: head is on top, foot is on bottom, "
        "face is on the front, body is on the back, left is on the left side, and right is on the right side. "
        "Roll the cube from the green tile to the red tile by following the arrow path. "
        "The upper-right card shows a target face. Will that target face be on top when the cube reaches the red tile? "
        "Answer yes or no."
    )


def make_record(seed: int, index: int, image_rel: str, puzzle) -> dict:
    return {
        "id": f"r_haimian_flip_{seed}-{index:05d}",
        "media": [image_rel],
        "messages": [
            {
                "role": "user",
                "question": build_question(),
                "answer": "",
                "options": {},
                "choices": ["yes", "no"],
                "hint": "",
            }
        ],
        "metadata": {
            "classification": classification(),
            "provenance": {
                "source": "original/批次04-0519.md",
                "method": "deterministic_cube_roll_simulation",
                "seed": seed,
                "index": index,
                "seed_description": "Square board with a fixed start orientation, arrow path, and target face card.",
                "generator": f"{SCRIPT_NAME}@{VERSION}({GAME_VERSION},{GENERATOR_TAG})",
                "rule_source": RULE_SOURCE,
            },
            "gt": {
                "answer": puzzle.answer,
                "answer_text": puzzle.answer,
                "answer_type": "yes_no",
                "choices": ["yes", "no"],
                "validator": {"kind": "exact_match", "solution": puzzle.answer},
            },
            "instance": {
                "difficulty": "medium",
                "complexity_score": 0.63,
                "tags": ["spongebob", "cube-roll", "orientation", "path-following"],
                "raw_state": puzzle_to_dict(puzzle),
            },
        },
    }


def generate(out_dir: Path, seed: int) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    for index, force_answer in enumerate((True, False)):
        puzzle_seed = rng.randint(10_000_000, 999_999_999)
        puzzle = generate_puzzle(puzzle_seed, force_answer=force_answer)
        image_rel = f"images/{index:05d}.png"
        render_puzzle(puzzle, out_dir / image_rel)
        records.append(make_record(seed, index, image_rel, puzzle))

    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl(
        [
            {
                "id": "haimian_flip.rule",
                "task": "spongebob_cube_orientation",
                "rule": "The cube starts with a fixed face assignment and changes top/front/left faces deterministically when rolled along the shown arrow path.",
            }
        ],
        out_dir / "rules.jsonl",
    )
    quality = []
    for row in records:
        answer = row["metadata"]["instance"]["raw_state"]["answer"]
        quality.append({"id": row["id"], "keep": answer == row["metadata"]["gt"]["answer"], "answer": answer})
    (out_dir / "quality_report.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "dataset": "haimian_flip_vqa",
        "version": VERSION,
        "generator": f"{SCRIPT_NAME}@{VERSION}({GENERATOR_TAG})",
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
    parser.add_argument("--out-dir", default="generated/haimian_flip_vqa")
    parser.add_argument("--seed", type=int, default=20260524)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.seed)
    print(f"Wrote {len(records)} haimian flip VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
