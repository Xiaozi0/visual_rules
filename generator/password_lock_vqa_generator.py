#!/usr/bin/env python3
"""Generate VQA samples for the batch-6 password-lock puzzle."""

from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


VERSION = "password_lock_v1.0.0"
SCRIPT_NAME = "password_lock_vqa_generator.py"
CANVAS = 720
RULE_SOURCE = "original/批次6-0522.md:解开密码锁"
REFERENCE_IMAGE = "original/assets/batch6_0522/lock_q1.png"

BG = (250, 248, 242)
PANEL = (255, 255, 255)
GRID = (218, 222, 228)
INK = (30, 34, 42)
LINE = (145, 29, 47)
BLUE = (42, 111, 190)
GRAY = (118, 126, 140)
EMPTY = (198, 204, 214)


@dataclass(frozen=True)
class LockClue:
    guess: Tuple[int, int, int]
    in_place: int
    misplaced: int


@dataclass(frozen=True)
class LockState:
    clues: List[LockClue]
    answer: Tuple[int, int, int]


def get_font(size: int) -> ImageFont.ImageFont:
    for name in ("Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int) -> None:
    font = get_font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0, y0, x1, y1 = box
    draw.text((x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2 - 2), text, fill=INK, font=font)


def score_guess(answer: Tuple[int, int, int], guess: Tuple[int, int, int]) -> Tuple[int, int]:
    in_place = sum(a == g for a, g in zip(answer, guess))
    common = len(set(answer).intersection(guess))
    return in_place, common - in_place


def candidates_for_clues(clues: Sequence[LockClue]) -> List[Tuple[int, int, int]]:
    candidates = []
    for code in itertools.permutations(range(10), 3):
        if all(score_guess(code, clue.guess) == (clue.in_place, clue.misplaced) for clue in clues):
            candidates.append(code)
    return candidates


def find_clues_for_answer(rng: random.Random, answer: Tuple[int, int, int]) -> List[LockClue]:
    all_guesses = [g for g in itertools.permutations(range(10), 3) if g != answer]
    rng.shuffle(all_guesses)

    clues_by_score: Dict[Tuple[int, int], List[LockClue]] = {}
    for guess in all_guesses:
        score = score_guess(answer, guess)
        if score == (3, 0):
            continue
        clues_by_score.setdefault(score, []).append(LockClue(guess, score[0], score[1]))

    preferred_scores = [(1, 0), (0, 1), (0, 2), (0, 0), (0, 1)]
    pool = []
    for score in preferred_scores:
        bucket = clues_by_score.get(score, [])
        if bucket:
            pool.append(rng.choice(bucket))
    pool.extend(LockClue(g, *score_guess(answer, g)) for g in all_guesses[:80])

    for size in range(4, 6):
        for combo in itertools.combinations(pool[:45], size):
            clues = list(combo)
            if len({clue.guess for clue in clues}) != len(clues):
                continue
            if candidates_for_clues(clues) == [answer]:
                rng.shuffle(clues)
                return clues
    raise RuntimeError(f"could not build unique clues for answer {answer}")


def build_state(rng: random.Random, use_reference: bool = False) -> LockState:
    if use_reference:
        # Original batch-6 example pattern, answer 042.
        clues = [
            LockClue((6, 8, 2), 1, 0),
            LockClue((6, 1, 4), 0, 1),
            LockClue((2, 0, 6), 0, 2),
            LockClue((7, 3, 8), 0, 0),
            LockClue((8, 7, 0), 0, 1),
        ]
        rng.shuffle(clues)
        answer = (0, 4, 2)
    else:
        answer = tuple(rng.sample(range(10), 3))
        clues = find_clues_for_answer(rng, answer)
    if candidates_for_clues(clues) != [answer]:
        raise RuntimeError("generated lock puzzle is not unique")
    return LockState(clues, answer)


def render_state(state: LockState, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)
    top = 72
    bottom = CANVAS - 72
    draw.rounded_rectangle((58, top, CANVAS - 58, bottom), radius=12, fill=PANEL, outline=GRID, width=3)

    row_gap = 95 if len(state.clues) <= 5 else 80
    start_y = 125 if len(state.clues) <= 5 else 105
    col_x = [110, 180, 250]
    for i, clue in enumerate(state.clues):
        y = start_y + i * row_gap
        for j, digit in enumerate(clue.guess):
            x = col_x[j]
            draw.rounded_rectangle((x, y, x + 50, y + 62), radius=8, fill=(255, 255, 255), outline=LINE, width=3)
            draw_centered_text(draw, (x, y, x + 50, y + 62), str(digit), 26)

        info_x = 355
        draw.rounded_rectangle((info_x, y, info_x + 250, y + 62), radius=8, fill=(247, 248, 250), outline=GRID, width=2)
        for dot in range(3):
            cx = info_x + 38 + dot * 34
            cy = y + 22
            if dot < clue.in_place:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=BLUE, outline=BLUE, width=2)
            else:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=EMPTY, width=2)
        for dot in range(3):
            cx = info_x + 38 + dot * 34
            cy = y + 44
            if dot < clue.misplaced:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=GRAY, width=4)
            else:
                draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=EMPTY, width=2)

    image.save(path)


def solve(state: LockState) -> str:
    candidates = candidates_for_clues(state.clues)
    if len(candidates) != 1:
        raise ValueError(f"not unique: {candidates}")
    return "".join(str(digit) for digit in candidates[0])


def raw_state(state: LockState) -> Dict:
    return {
        "question_kind": "password_lock",
        "distinct_digits": True,
        "clues": [
            {"guess": list(clue.guess), "in_place": clue.in_place, "misplaced": clue.misplaced}
            for clue in state.clues
        ],
        "solution_count": len(candidates_for_clues(state.clues)),
    }


def make_record(idx: int, seed: int, state: LockState, answer: str, media_path: str) -> Dict:
    return {
        "id": f"r_password_lock_v1-{seed}-{idx:05d}",
        "media": [media_path],
        "messages": [
            {
                "role": "user",
                "question": (
                    "<image> Solve the three-digit password lock. Each row shows a guess. To the "
                    "right of each guess, the top row of blue filled dots gives how many digits "
                    "are correct and in the same position; the bottom row of gray outlined dots "
                    "gives how many digits are in the code but in different positions. The code "
                    "has three distinct digits. What is the code? Answer with digits only."
                ),
                "answer": answer,
                "options": {},
                "choices": [],
                "hint": "",
            }
        ],
        "metadata": {
            "classification": {
                "domain": "logic_puzzles",
                "task": "password_lock",
                "reasoning_type": "constraint_satisfaction",
                "visual_type": "symbol_panel",
                "rule_delivery_mode": "explicit_text_prompt",
            },
            "dataset": {
                "slug": "password_lock_v1",
                "source_id": "batch6_0522_password_lock",
                "family": "visual_logic_puzzles",
                "upstream_name": "original/批次6-0522.md",
                "title": "Password Lock VQA",
                "version": VERSION,
            },
            "provenance": {
                "source": RULE_SOURCE,
                "method": "deterministic_constraint_generation",
                "seed": seed,
                "index": idx,
                "seed_description": "Three-digit lock with positional and misplaced digit count clues.",
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE,
                "reference_image": REFERENCE_IMAGE,
            },
            "gt": {
                "answer": answer,
                "answer_text": answer,
                "answer_type": "string",
                "choices": [],
                "validator": {"kind": "exact_match", "solution": answer},
            },
            "instance": {
                "difficulty": "hard",
                "complexity_score": 0.74,
                "reasoning_depth": len(state.clues),
                "visual_load": len(state.clues) / 5,
                "tags": ["batch6", "password-lock", "constraint-satisfaction", "code"],
                "raw_state": raw_state(state),
            },
        },
    }


def write_jsonl(records: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_rules(path: Path) -> None:
    rules = [
        {"id": "password_lock_v1.code", "task": "password_lock", "rule": "The hidden code has three distinct digits."},
        {"id": "password_lock_v1.in_place", "task": "password_lock", "rule": "Blue filled dots count digits that are correct and in the same position."},
        {"id": "password_lock_v1.misplaced", "task": "password_lock", "rule": "Gray outlined dots count digits that are in the code but in different positions."},
        {"id": "password_lock_v1.unique", "task": "password_lock", "rule": "The puzzle must have exactly one code satisfying all clues."},
    ]
    write_jsonl(rules, path)


def verify_record(record: Dict) -> bool:
    raw = record["metadata"]["instance"]["raw_state"]
    clues = [
        LockClue(tuple(item["guess"]), item["in_place"], item["misplaced"])
        for item in raw["clues"]
    ]
    state = LockState(clues, (0, 0, 0))
    answer = solve(state)
    return answer == record["metadata"]["gt"]["answer"] == record["messages"][0]["answer"]


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    if count < 1:
        raise ValueError("count must be positive")
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    for idx in range(count):
        sample_seed = rng.randint(10_000_000, 999_999_999)
        state = build_state(random.Random(sample_seed), use_reference=(idx == 0))
        answer = solve(state)
        image_name = f"{idx:05d}.png"
        render_state(state, image_dir / image_name)
        records.append(make_record(idx, sample_seed, state, answer, f"images/{image_name}"))

    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_rules(out_dir / "rules.jsonl")
    quality = [
        {
            "id": record["id"],
            "keep": verify_record(record),
            "reason": "constraint solver exact-match recomputation",
            "answer": record["metadata"]["gt"]["answer"],
        }
        for record in records
    ]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "dataset": "password_lock_v1",
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
    parser.add_argument("--out-dir", default="generated/password_lock_v1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260522)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.count, args.seed)
    print(f"Wrote {len(records)} Password Lock VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
