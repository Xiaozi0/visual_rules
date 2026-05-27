#!/usr/bin/env python3
"""Generate deterministic VQA samples for the Memory Puzzle game clone.

The script renders square, text-free card grids and emits JSONL records in the
project VQA format. The verifier uses the board state directly: each icon is a
shape/color tuple and a pair matches only when both fields are identical.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw


VERSION = "memory_puzzle_v1.0.0"
SCRIPT_NAME = "memory_puzzle_vqa_generator.py"
CANVAS = 600
ROWS = 4
COLS = 4
CELL = CANVAS // COLS
CARD_MARGIN = 16
RULE_SOURCE = "original/批次 5-0521.md:Memory Puzzle; vendor/memory_puzzle/memorypuzzle.py"

BG = (28, 35, 50)
GRID_LINE = (54, 65, 86)
CARD_BACK = (236, 239, 245)
CARD_EDGE = (42, 52, 70)
CARD_FRONT = (251, 252, 255)
INK = (26, 30, 38)
HIGHLIGHT = (255, 203, 92)

COLORS = {
    "red": (224, 67, 73),
    "green": (58, 164, 105),
    "blue": (64, 116, 214),
    "orange": (236, 137, 50),
    "purple": (141, 87, 183),
    "cyan": (48, 168, 190),
    "yellow": (226, 191, 61),
    "pink": (224, 92, 150),
}
SHAPES = ["circle", "square", "diamond", "oval", "triangle", "cross", "star", "bars"]


@dataclass(frozen=True)
class Icon:
    shape: str
    color: str


@dataclass(frozen=True)
class Card:
    row: int
    col: int
    icon: Icon
    revealed: bool
    selected: bool = False


@dataclass(frozen=True)
class MemoryState:
    rows: int
    cols: int
    cards: List[Card]
    question_kind: str
    selected_positions: List[Tuple[int, int]]


def card_at(state: MemoryState, row: int, col: int) -> Card:
    for card in state.cards:
        if card.row == row and card.col == col:
            return card
    raise KeyError((row, col))


def is_match(a: Card, b: Card) -> bool:
    return a.icon == b.icon


def visible_pair_count(state: MemoryState) -> int:
    counts: Dict[Tuple[str, str], int] = {}
    for card in state.cards:
        if card.revealed:
            key = (card.icon.shape, card.icon.color)
            counts[key] = counts.get(key, 0) + 1
    return sum(count // 2 for count in counts.values())


def cell_bounds(row: int, col: int) -> Tuple[int, int, int, int]:
    x0 = col * CELL + CARD_MARGIN
    y0 = row * CELL + CARD_MARGIN
    x1 = (col + 1) * CELL - CARD_MARGIN
    y1 = (row + 1) * CELL - CARD_MARGIN
    return x0, y0, x1, y1


def draw_icon(draw: ImageDraw.ImageDraw, icon: Icon, bounds: Tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = bounds
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    w = x1 - x0
    h = y1 - y0
    r = min(w, h) // 4
    color = COLORS[icon.color]
    if icon.shape == "circle":
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=INK, width=3)
    elif icon.shape == "square":
        draw.rectangle((cx - r, cy - r, cx + r, cy + r), fill=color, outline=INK, width=3)
    elif icon.shape == "diamond":
        draw.polygon([(cx, cy - r - 8), (cx + r + 8, cy), (cx, cy + r + 8), (cx - r - 8, cy)], fill=color, outline=INK)
        draw.line([(cx, cy - r - 8), (cx + r + 8, cy), (cx, cy + r + 8), (cx - r - 8, cy), (cx, cy - r - 8)], fill=INK, width=3)
    elif icon.shape == "oval":
        draw.ellipse((cx - r - 18, cy - r, cx + r + 18, cy + r), fill=color, outline=INK, width=3)
    elif icon.shape == "triangle":
        draw.polygon([(cx, cy - r - 12), (cx + r + 14, cy + r + 8), (cx - r - 14, cy + r + 8)], fill=color, outline=INK)
        draw.line([(cx, cy - r - 12), (cx + r + 14, cy + r + 8), (cx - r - 14, cy + r + 8), (cx, cy - r - 12)], fill=INK, width=3)
    elif icon.shape == "cross":
        t = r // 2
        points = [
            (cx - t, cy - r - 14), (cx + t, cy - r - 14), (cx + t, cy - t),
            (cx + r + 14, cy - t), (cx + r + 14, cy + t), (cx + t, cy + t),
            (cx + t, cy + r + 14), (cx - t, cy + r + 14), (cx - t, cy + t),
            (cx - r - 14, cy + t), (cx - r - 14, cy - t), (cx - t, cy - t),
        ]
        draw.polygon(points, fill=color, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=3)
    elif icon.shape == "star":
        points = []
        for i in range(10):
            radius = r + 16 if i % 2 == 0 else r // 2
            angle = -90 + i * 36
            import math
            points.append((cx + radius * math.cos(math.radians(angle)), cy + radius * math.sin(math.radians(angle))))
        draw.polygon(points, fill=color, outline=INK)
        draw.line(points + [points[0]], fill=INK, width=3)
    elif icon.shape == "bars":
        for offset in [-22, 0, 22]:
            draw.rounded_rectangle((cx - r - 16, cy + offset - 7, cx + r + 16, cy + offset + 7), radius=4, fill=color, outline=INK, width=2)


def render_state(state: MemoryState, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)
    for pos in range(0, CANVAS + 1, CELL):
        draw.line((pos, 0, pos, CANVAS), fill=GRID_LINE, width=1)
        draw.line((0, pos, CANVAS, pos), fill=GRID_LINE, width=1)
    for card in state.cards:
        bounds = cell_bounds(card.row, card.col)
        x0, y0, x1, y1 = bounds
        outline = HIGHLIGHT if card.selected else CARD_EDGE
        width = 6 if card.selected else 3
        if card.revealed:
            draw.rounded_rectangle(bounds, radius=10, fill=CARD_FRONT, outline=outline, width=width)
            draw_icon(draw, card.icon, bounds)
        else:
            draw.rounded_rectangle(bounds, radius=10, fill=CARD_BACK, outline=outline, width=width)
            inset = 22
            draw.rounded_rectangle((x0 + inset, y0 + inset, x1 - inset, y1 - inset), radius=8, outline=(96, 111, 138), width=4)
            draw.line((x0 + 32, y0 + 32, x1 - 32, y1 - 32), fill=(96, 111, 138), width=4)
            draw.line((x0 + 32, y1 - 32, x1 - 32, y0 + 32), fill=(96, 111, 138), width=4)
    image.save(path)


def make_board(rng: random.Random) -> List[Card]:
    icons = [Icon(shape, color) for shape, color in zip(SHAPES, COLORS.keys())]
    deck = icons[:8] * 2
    rng.shuffle(deck)
    cards = []
    for idx, icon in enumerate(deck):
        row, col = divmod(idx, COLS)
        cards.append(Card(row=row, col=col, icon=icon, revealed=False))
    return cards


def set_revealed(cards: List[Card], positions: Sequence[Tuple[int, int]], selected: Sequence[Tuple[int, int]] = ()) -> List[Card]:
    pos_set = set(positions)
    sel_set = set(selected)
    return [
        Card(card.row, card.col, card.icon, (card.row, card.col) in pos_set, (card.row, card.col) in sel_set)
        for card in cards
    ]


def positions_by_icon(cards: Sequence[Card]) -> Dict[Icon, List[Tuple[int, int]]]:
    result: Dict[Icon, List[Tuple[int, int]]] = {}
    for card in cards:
        result.setdefault(card.icon, []).append((card.row, card.col))
    return result


def build_visible_pairs_state(rng: random.Random) -> MemoryState:
    base = make_board(rng)
    grouped = list(positions_by_icon(base).values())
    rng.shuffle(grouped)
    revealed = list(grouped[0]) + list(grouped[1])
    revealed += [grouped[2][0], grouped[3][0], grouped[4][0], grouped[5][0]]
    cards = set_revealed(base, revealed)
    return MemoryState(ROWS, COLS, cards, "visible_pair_count", [])


def build_selected_match_state(rng: random.Random) -> MemoryState:
    base = make_board(rng)
    grouped = list(positions_by_icon(base).values())
    rng.shuffle(grouped)
    make_match = rng.choice([True, False])
    selected = list(grouped[0]) if make_match else [grouped[0][0], grouped[1][0]]
    revealed = selected + [grouped[2][0], grouped[3][0], grouped[4][0]]
    cards = set_revealed(base, revealed, selected)
    return MemoryState(ROWS, COLS, cards, "selected_match", selected)


def solve(state: MemoryState) -> str:
    if state.question_kind == "visible_pair_count":
        return str(visible_pair_count(state))
    if state.question_kind == "selected_match":
        a_pos, b_pos = state.selected_positions
        return "yes" if is_match(card_at(state, *a_pos), card_at(state, *b_pos)) else "no"
    raise ValueError(state.question_kind)


def raw_state(state: MemoryState) -> Dict:
    return {
        "grid_size": [state.rows, state.cols],
        "question_kind": state.question_kind,
        "selected_positions": state.selected_positions,
        "cards": [
            {
                "row": card.row,
                "col": card.col,
                "shape": card.icon.shape,
                "color": card.icon.color,
                "revealed": card.revealed,
                "selected": card.selected,
            }
            for card in state.cards
        ],
    }


def make_record(idx: int, seed: int, state: MemoryState, answer: str, media_path: str) -> Dict:
    if state.question_kind == "visible_pair_count":
        question = (
            "<image> This is a Memory Puzzle board. Face-up cards show their shape and color; "
            "face-down cards hide their icons. A matching pair means two face-up cards with the "
            "same shape and the same color. How many matching pairs are currently visible? "
            "Answer with a number only."
        )
        choices = ["0", "1", "2", "3", "4"]
        answer_type = "count"
        difficulty = "medium"
        complexity = 0.45
        reasoning_depth = 1
    elif state.question_kind == "selected_match":
        question = (
            "<image> This is a Memory Puzzle board. The two yellow-outlined face-up cards are "
            "the selected cards. Do they match exactly in both shape and color? Answer only yes or no."
        )
        choices = ["yes", "no"]
        answer_type = "yes_no"
        difficulty = "easy"
        complexity = 0.3
        reasoning_depth = 1
    else:
        raise ValueError(state.question_kind)

    return {
        "id": f"r_memory_puzzle_v1-{seed}-{idx:05d}",
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
                "domain": "games",
                "task": "memory_puzzle_pair_matching",
                "reasoning_type": "deductive",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt",
            },
            "dataset": {
                "slug": "memory_puzzle_v1",
                "source_id": "invent_with_python_memory_puzzle",
                "family": "card_matching_static_board",
                "upstream_name": "Invent with Python Memory Puzzle",
                "title": "Memory Puzzle Pair Matching VQA",
                "version": VERSION,
            },
            "provenance": {
                "source": "https://inventwithpython.com/blog/i-need-practice-programming-49-ideas-for-game-clones-to-code.html#memorypuzzle",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "4x4 memory-card board with paired shape/color icons and a revealed-card mask.",
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE,
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
                "visual_load": sum(1 for card in state.cards if card.revealed) / len(state.cards),
                "tags": ["memory-puzzle", "pair-matching", "grid-board", "shape-color"],
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
        {"id": "memory_puzzle_v1.board", "task": "memory_puzzle_pair_matching", "rule": "The board is a grid of cards; unrevealed cards hide their icons."},
        {"id": "memory_puzzle_v1.icons", "task": "memory_puzzle_pair_matching", "rule": "Each icon is defined by both a shape and a color."},
        {"id": "memory_puzzle_v1.match", "task": "memory_puzzle_pair_matching", "rule": "Two cards match only if both the shape and color are identical."},
    ]
    write_jsonl(rules, path)


def verify_record(record: Dict) -> bool:
    raw = record["metadata"]["instance"]["raw_state"]
    cards = [
        Card(item["row"], item["col"], Icon(item["shape"], item["color"]), item["revealed"], item["selected"])
        for item in raw["cards"]
    ]
    state = MemoryState(raw["grid_size"][0], raw["grid_size"][1], cards, raw["question_kind"], [tuple(p) for p in raw["selected_positions"]])
    return solve(state) == record["metadata"]["gt"]["answer"] == record["messages"][0]["answer"]


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    if count < 1:
        raise ValueError("count must be positive")
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    builders = [build_visible_pairs_state, build_selected_match_state]
    records = []
    for idx in range(count):
        sample_seed = rng.randint(10_000_000, 999_999_999)
        state = builders[idx % len(builders)](random.Random(sample_seed))
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
            "reason": "rule verifier exact-match recomputation",
            "answer": record["metadata"]["gt"]["answer"],
        }
        for record in records
    ]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "dataset": "memory_puzzle_v1",
        "version": VERSION,
        "generator": SCRIPT_NAME,
        "count": len(records),
        "seed": seed,
        "build_complexity": "low",
        "reasoning_max": "medium",
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
    parser.add_argument("--out-dir", default="generated/memory_puzzle_v1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260521)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.count, args.seed)
    print(f"Wrote {len(records)} Memory Puzzle VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
