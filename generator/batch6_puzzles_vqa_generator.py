#!/usr/bin/env python3
"""Generate deterministic VQA samples for selected puzzles from batch 6.

The implemented puzzle types are:
- segment_count_code: infer a numeric code by counting line segments in each symbol.
- three_digit_lock: solve a Mastermind-style 3-digit lock from positional clues.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


VERSION = "batch6_puzzles_v1.0.0"
SCRIPT_NAME = "batch6_puzzles_vqa_generator.py"
CANVAS = 720
RULE_SOURCE = "original/批次6-0522.md"
SOURCE_URLS = [
    "https://gitee.com/ye-zixiao/myob_pic/raw/master/20260522220645666.png",
    "https://gitee.com/ye-zixiao/myob_pic/raw/master/20260522214928804.png",
]

BG = (250, 248, 242)
INK = (30, 34, 42)
LINE = (145, 29, 47)
MUTED = (96, 104, 118)
PANEL = (255, 255, 255)
GRID = (218, 222, 228)
ACCENT = (42, 111, 190)
MISPLACED = (118, 126, 140)


@dataclass(frozen=True)
class SegmentSymbol:
    name: str
    segments: List[Tuple[int, int, int, int]]


@dataclass(frozen=True)
class SegmentState:
    symbols: List[SegmentSymbol]


@dataclass(frozen=True)
class LockClue:
    guess: Tuple[int, int, int]
    correct_position: int
    wrong_position: int


@dataclass(frozen=True)
class LockState:
    clues: List[LockClue]
    answer: Tuple[int, int, int]


SEGMENT_LIBRARY = {
    3: [
        (10, 12, 86, 12),
        (86, 12, 86, 88),
        (10, 88, 86, 88),
    ],
    4: [
        (12, 12, 12, 88),
        (12, 50, 86, 50),
        (86, 12, 86, 88),
        (12, 88, 86, 88),
    ],
    5: [
        (12, 12, 86, 12),
        (12, 12, 12, 88),
        (12, 50, 86, 50),
        (86, 50, 86, 88),
        (12, 88, 86, 88),
    ],
    6: [
        (12, 12, 86, 12),
        (12, 12, 12, 88),
        (12, 50, 86, 50),
        (12, 88, 86, 88),
        (86, 12, 86, 50),
        (86, 50, 86, 88),
    ],
    7: [
        (12, 12, 86, 12),
        (86, 12, 86, 88),
        (12, 50, 86, 50),
        (12, 12, 12, 50),
        (12, 88, 86, 88),
        (48, 12, 48, 88),
        (12, 88, 48, 50),
    ],
    8: [
        (12, 12, 86, 12),
        (12, 88, 86, 88),
        (12, 12, 12, 88),
        (86, 12, 86, 88),
        (12, 50, 86, 50),
        (12, 12, 86, 88),
        (86, 12, 12, 88),
        (48, 12, 48, 88),
    ],
}


def get_font(size: int) -> ImageFont.ImageFont:
    for name in ("Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK) -> None:
    font = get_font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0, y0, x1, y1 = box
    draw.text((x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2 - 2), text, fill=fill, font=font)


def transform_segment(seg: Tuple[int, int, int, int], x: int, y: int, scale: float) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = seg
    return (int(x + x0 * scale), int(y + y0 * scale), int(x + x1 * scale), int(y + y1 * scale))


def render_segment_state(state: SegmentState, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((50, 180, CANVAS - 50, 500), radius=12, fill=PANEL, outline=GRID, width=3)
    draw.line((80, 470, CANVAS - 80, 470), fill=GRID, width=2)
    slot_w = 150
    start_x = 95
    for idx, symbol in enumerate(state.symbols):
        x = start_x + idx * slot_w
        y = 245
        draw.rounded_rectangle((x - 20, y - 35, x + 125, y + 140), radius=10, outline=GRID, width=2)
        for seg in symbol.segments:
            draw.line(transform_segment(seg, x, y, 1.15), fill=LINE, width=8)
    image.save(path)


def segment_answer(state: SegmentState) -> str:
    return "".join(str(len(symbol.segments)) for symbol in state.symbols)


def build_segment_state(rng: random.Random) -> SegmentState:
    code = rng.choice([(6, 5, 8, 7), (4, 7, 6, 5), (8, 3, 5, 6), (5, 6, 4, 8)])
    symbols = []
    for idx, digit in enumerate(code):
        segs = list(SEGMENT_LIBRARY[digit])
        # Keep the count unchanged while changing draw order for visual variety.
        rng.shuffle(segs)
        symbols.append(SegmentSymbol(f"s{idx}", segs))
    return SegmentState(symbols)


def score_guess(answer: Tuple[int, int, int], guess: Tuple[int, int, int]) -> Tuple[int, int]:
    correct_position = sum(a == g for a, g in zip(answer, guess))
    answer_counts: Dict[int, int] = {}
    guess_counts: Dict[int, int] = {}
    for digit in answer:
        answer_counts[digit] = answer_counts.get(digit, 0) + 1
    for digit in guess:
        guess_counts[digit] = guess_counts.get(digit, 0) + 1
    common = sum(min(answer_counts.get(d, 0), guess_counts.get(d, 0)) for d in guess_counts)
    return correct_position, common - correct_position


def candidates_for_clues(clues: Sequence[LockClue]) -> List[Tuple[int, int, int]]:
    result = []
    for code in itertools.permutations(range(10), 3):
        if all(score_guess(code, clue.guess) == (clue.correct_position, clue.wrong_position) for clue in clues):
            result.append(code)
    return result


def build_lock_state(rng: random.Random) -> LockState:
    # This pattern is based on the batch-6 lock puzzle and has a unique answer 042.
    base = [
        LockClue((6, 8, 2), 1, 0),
        LockClue((6, 1, 4), 0, 1),
        LockClue((2, 0, 6), 0, 2),
        LockClue((7, 3, 8), 0, 0),
        LockClue((8, 7, 0), 0, 1),
    ]
    answer = (0, 4, 2)
    clues = list(base)
    rng.shuffle(clues)
    assert candidates_for_clues(clues) == [answer]
    return LockState(clues, answer)


def render_lock_state(state: LockState, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((58, 72, CANVAS - 58, CANVAS - 72), radius=12, fill=PANEL, outline=GRID, width=3)
    col_x = [110, 180, 250]
    for i, clue in enumerate(state.clues):
        y = 130 + i * 95
        for j, digit in enumerate(clue.guess):
            x = col_x[j]
            draw.rounded_rectangle((x, y, x + 50, y + 62), radius=8, fill=(255, 255, 255), outline=LINE, width=3)
            draw_centered_text(draw, (x, y, x + 50, y + 62), str(digit), 26, fill=INK)
        info_x = 355
        draw.rounded_rectangle((info_x, y, info_x + 250, y + 62), radius=8, fill=(247, 248, 250), outline=GRID, width=2)
        for dot in range(3):
            cx = info_x + 38 + dot * 34
            cy = y + 22
            if dot < clue.correct_position:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=ACCENT, outline=ACCENT, width=2)
            else:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=(198, 204, 214), width=2)
        for dot in range(3):
            cx = info_x + 38 + dot * 34
            cy = y + 44
            if dot < clue.wrong_position:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=MISPLACED, width=4)
            else:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=(198, 204, 214), width=2)
    image.save(path)


def lock_answer(state: LockState) -> str:
    cands = candidates_for_clues(state.clues)
    if len(cands) != 1:
        raise ValueError(f"lock puzzle not unique: {cands}")
    return "".join(str(d) for d in cands[0])


def make_record(idx: int, seed: int, kind: str, state, answer: str, media_path: str) -> Dict:
    if kind == "segment_count_code":
        question = (
            "<image> Each symbol is made only of straight line segments. The digit for a symbol "
            "is the number of visible line segments in that symbol. Read the four symbols from "
            "left to right. What is the four-digit code? Answer with digits only."
        )
        choices = []
        answer_type = "string"
        difficulty = "medium"
        complexity = 0.55
        reasoning_depth = 1
        visual_load = len(state.symbols) / 4
        raw = {
            "question_kind": kind,
            "symbols": [
                {"name": symbol.name, "segment_count": len(symbol.segments), "segments": symbol.segments}
                for symbol in state.symbols
            ],
        }
        tags = ["batch6", "segment-count", "code"]
    elif kind == "three_digit_lock":
        question = (
            "<image> Solve the three-digit lock. Each row shows a guess. To the right of each "
            "guess, the top row of blue filled dots gives how many digits are correct and in the "
            "same position; the bottom row of gray outlined dots gives how many digits are in "
            "the code but in different positions. The code has three distinct digits. What is "
            "the code? Answer with digits only."
        )
        choices = []
        answer_type = "string"
        difficulty = "hard"
        complexity = 0.72
        reasoning_depth = len(state.clues)
        visual_load = len(state.clues) / 5
        raw = {
            "question_kind": kind,
            "distinct_digits": True,
            "clues": [
                {
                    "guess": list(clue.guess),
                    "correct_position": clue.correct_position,
                    "wrong_position": clue.wrong_position,
                }
                for clue in state.clues
            ],
            "solution_count": len(candidates_for_clues(state.clues)),
        }
        tags = ["batch6", "logic-lock", "constraint-satisfaction"]
    else:
        raise ValueError(kind)

    return {
        "id": f"r_batch6_puzzles_v1-{seed}-{idx:05d}",
        "media": [media_path],
        "messages": [
            {
                "role": "user",
                "question": question,
                "answer": answer,
                "options": {},
                "choices": choices,
                "hint": "",
            }
        ],
        "metadata": {
            "classification": {
                "domain": "logic_puzzles",
                "task": kind,
                "reasoning_type": "constraint_satisfaction" if kind == "three_digit_lock" else "numerical",
                "visual_type": "symbol_panel",
                "rule_delivery_mode": "explicit_text_prompt",
            },
            "dataset": {
                "slug": "batch6_puzzles_v1",
                "source_id": "batch6_0522_puzzles",
                "family": "visual_logic_puzzles",
                "upstream_name": "original/批次6-0522.md",
                "title": "Batch 6 Visual Puzzle VQA",
                "version": VERSION,
            },
            "provenance": {
                "source": RULE_SOURCE,
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": f"{kind} synthetic puzzle instance.",
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE,
                "reference_images": SOURCE_URLS,
            },
            "gt": {
                "answer": answer,
                "answer_text": answer,
                "answer_type": answer_type,
                "choices": choices,
                "validator": {"kind": "exact_match", "solution": answer},
            },
            "instance": {
                "difficulty": difficulty,
                "complexity_score": complexity,
                "reasoning_depth": reasoning_depth,
                "visual_load": visual_load,
                "tags": tags,
                "raw_state": raw,
            },
        },
    }


def write_jsonl(records: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_rules(path: Path) -> None:
    rules = [
        {"id": "batch6_puzzles_v1.segment_count", "task": "segment_count_code", "rule": "The digit for each symbol is the number of visible straight line segments."},
        {"id": "batch6_puzzles_v1.lock_clues", "task": "three_digit_lock", "rule": "Each lock clue gives counts for correct-position and wrong-position digits."},
        {"id": "batch6_puzzles_v1.lock_unique", "task": "three_digit_lock", "rule": "The target lock code has distinct digits and exactly one solution."},
    ]
    write_jsonl(rules, path)


def verify_record(record: Dict) -> bool:
    raw = record["metadata"]["instance"]["raw_state"]
    if raw["question_kind"] == "segment_count_code":
        answer = "".join(str(item["segment_count"]) for item in raw["symbols"])
    elif raw["question_kind"] == "three_digit_lock":
        clues = [
            LockClue(tuple(item["guess"]), item["correct_position"], item["wrong_position"])
            for item in raw["clues"]
        ]
        cands = candidates_for_clues(clues)
        answer = "".join(str(d) for d in cands[0]) if len(cands) == 1 else ""
    else:
        return False
    return answer == record["metadata"]["gt"]["answer"] == record["messages"][0]["answer"]


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    if count < 1:
        raise ValueError("count must be positive")
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    builders = [
        ("segment_count_code", build_segment_state, segment_answer, render_segment_state),
        ("three_digit_lock", build_lock_state, lock_answer, render_lock_state),
    ]
    for idx in range(count):
        sample_seed = rng.randint(10_000_000, 999_999_999)
        kind, builder, solver, renderer = builders[idx % len(builders)]
        state = builder(random.Random(sample_seed))
        answer = solver(state)
        image_name = f"{idx:05d}.png"
        renderer(state, image_dir / image_name)
        records.append(make_record(idx, sample_seed, kind, state, answer, f"images/{image_name}"))

    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_rules(out_dir / "rules.jsonl")
    quality = [
        {
            "id": record["id"],
            "keep": verify_record(record),
            "reason": "rule verifier exact-match recomputation",
            "answer": record["metadata"]["gt"]["answer"],
        }
        for record in records
    ]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "dataset": "batch6_puzzles_v1",
        "version": VERSION,
        "generator": SCRIPT_NAME,
        "count": len(records),
        "seed": seed,
        "build_complexity": "low",
        "reasoning_max": "high",
        "rule_source": RULE_SOURCE,
        "format": "format_docs/VQA_DATA_FORMAT.md",
        "classification": "format_docs/classification.md",
        "reproduce_command": f"python3 generator/{SCRIPT_NAME} --count {len(records)} --seed {seed} --out-dir {out_dir}",
        "outputs": {
            "records": "vis_scaling_simple_mm.jsonl",
            "rules": "rules.jsonl",
            "quality_report": "quality_report.json",
            "images": "images/",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(item["keep"] for item in quality):
        raise RuntimeError("quality verification failed")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated/batch6_puzzles_v1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260522)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.count, args.seed)
    print(f"Wrote {len(records)} Batch 6 puzzle VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
