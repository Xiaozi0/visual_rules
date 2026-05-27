#!/usr/bin/env python3
"""Generate deterministic VQA samples for Grid Lock / Traffic Jam."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

from PIL import Image, ImageDraw

VERSION = "grid_lock_v1.0.0"
SCRIPT_NAME = "grid_lock_vqa_generator.py"
CANVAS = 600
N = 6
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Grid Lock"

COLORS = {
    "red": (220, 50, 50),
    "green": (50, 200, 50),
    "blue": (50, 100, 220),
    "yellow": (230, 200, 50),
    "purple": (150, 50, 200),
    "orange": (230, 130, 40),
    "cyan": (50, 200, 200),
    "pink": (230, 50, 150)
}
COLOR_NAMES = list(COLORS.keys())
BG = (240, 240, 240)
GRID = (200, 200, 200)

@dataclass
class Vehicle:
    color: str
    r: int
    c: int
    length: int
    horizontal: bool

@dataclass
class GridLockState:
    kind: str
    vehicles: List[Vehicle]
    blocking_color: str | None
    is_clear: bool

def build_state(rng: random.Random, kind: str) -> GridLockState:
    board = [[None for _ in range(N)] for _ in range(N)]
    vehicles = []
    
    # Target car (Red) is always at row 2, horizontal
    red_c = rng.randint(0, 2)
    red = Vehicle("red", 2, red_c, 2, True)
    vehicles.append(red)
    for i in range(2): board[2][red_c + i] = "red"
    
    # Add blocking vehicle in row 2
    block_c = rng.randint(red_c + 2, 5)
    block_len = rng.randint(2, 3)
    block_r = block_c # vertical block
    # Vertical blocking car/truck crossing row 2
    v_r = rng.randint(max(0, 2 - block_len + 1), min(N - block_len, 2))
    block_v = Vehicle("blue", v_r, block_c, block_len, False)
    vehicles.append(block_v)
    for i in range(block_len): board[v_r + i][block_c] = "blue"
    
    # Add some random others
    colors = [c for c in COLOR_NAMES if c not in ["red", "blue"]]
    for color in colors:
        for _ in range(10): # attempts
            horizontal = rng.choice([True, False])
            length = rng.randint(2, 3)
            if horizontal:
                r, c = rng.randint(0, N-1), rng.randint(0, N-length)
                if r == 2: continue # avoid target row for simplicity
                if all(board[r][c+i] is None for i in range(length)):
                    vehicles.append(Vehicle(color, r, c, length, True))
                    for i in range(length): board[r][c+i] = color
                    break
            else:
                r, c = rng.randint(0, N-length), rng.randint(0, N-1)
                if all(board[r+i][c] is None for i in range(length)):
                    vehicles.append(Vehicle(color, r, c, length, False))
                    for i in range(length): board[r+i][c] = color
                    break
                    
    # Find blocking vehicle
    blocking_color = "blue"
    # Check if path is clear if blue moves
    is_clear = True
    for c in range(block_c + 1, N):
        if board[2][c] is not None:
            is_clear = False
            break
            
    return GridLockState(kind, vehicles, blocking_color, is_clear)

def solve(state: GridLockState) -> str:
    if state.kind == "who_blocks":
        return state.blocking_color if state.blocking_color else "none"
    elif state.kind == "is_clear_after":
        return "yes" if state.is_clear else "no"
    raise ValueError(state.kind)

def render(state: GridLockState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=GRID, width=1)
        draw.line((0, p, CANVAS, p), fill=GRID, width=1)
        
    # Draw exit
    draw.rectangle((CANVAS - 10, 2 * CELL + 10, CANVAS, 3 * CELL - 10), fill=(0, 0, 0))
    
    for v in state.vehicles:
        color = COLORS[v.color]
        if v.horizontal:
            draw.rounded_rectangle((v.c * CELL + 5, v.r * CELL + 10, (v.c + v.length) * CELL - 5, (v.r + 1) * CELL - 10), radius=10, fill=color, outline=(0,0,0), width=2)
        else:
            draw.rounded_rectangle((v.c * CELL + 10, v.r * CELL + 5, (v.c + 1) * CELL - 10, (v.r + v.length) * CELL - 5), radius=10, fill=color, outline=(0,0,0), width=2)
            
    img.save(path)

def record(idx: int, seed: int, state: GridLockState, answer: str, media: str) -> Dict:
    if state.kind == "who_blocks":
        q = "<image> This is a 6x6 Grid Lock board. The goal is to get the Red car to the exit on the right. Which color vehicle is directly blocking the Red car's path to the exit?"
        atype, diff, score = "string", "easy", 0.4
    else:
        q = f"<image> This is a 6x6 Grid Lock board. If the {state.blocking_color} vehicle moves out of the way, will the Red car have a completely clear path to the exit? Answer only yes or no."
        atype, diff, score = "yes_no", "medium", 0.6
        
    return {
        "id": f"r_grid_lock_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": [], "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "grid_lock_logic",
                "reasoning_type": "spatial",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "grid_lock_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Grid Lock",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE
            },
            "gt": {
                "answer": answer,
                "answer_text": answer,
                "answer_type": atype,
                "validator": {"kind": "exact_match", "solution": answer}
            },
            "instance": {
                "difficulty": diff,
                "complexity_score": score,
                "reasoning_depth": 1,
                "visual_load": 0.5,
                "tags": ["grid-lock", "traffic-jam", "blocking", "pathfinding"],
                "raw_state": {
                    "vehicles": [vars(v) for v in state.vehicles],
                    "blocking_color": state.blocking_color,
                    "is_clear": state.is_clear
                }
            }
        }
    }

def write_jsonl(items: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    for idx in range(count):
        s = rng.randint(10_000_000, 999_999_999)
        kind = ["who_blocks", "is_clear_after"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "grid_lock_v1.movement", "rule": "Vehicles can only move forward or backward along their length."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "grid_lock_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "medium", "reasoning_max": "medium", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/grid_lock_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Grid Lock VQA records to {a.out_dir}")

if __name__ == "__main__": main()
