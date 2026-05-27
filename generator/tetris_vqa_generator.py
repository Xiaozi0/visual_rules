#!/usr/bin/env python3
"""Generate deterministic VQA samples for Tetris."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

from PIL import Image, ImageDraw

VERSION = "tetris_v1.0.0"
SCRIPT_NAME = "tetris_vqa_generator.py"
CANVAS = 600
N_COLS = 10
N_ROWS = 12
CELL = CANVAS // N_COLS
RULE_SOURCE = "original/批次 5-0521.md:Tetris"

# Colors for pieces
COLORS = {
    "I": (50, 200, 200),
    "O": (200, 200, 50),
    "T": (150, 50, 200),
    "S": (50, 200, 50),
    "Z": (200, 50, 50),
    "J": (50, 100, 200),
    "L": (200, 150, 50)
}
BG = (20, 20, 30)
GRID = (40, 40, 60)
HIGHLIGHT = (255, 255, 255)

PIECES = {
    "I": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "T": [(0, 1), (1, 0), (1, 1), (1, 2)],
    "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
    "Z": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "L": [(0, 2), (1, 0), (1, 1), (1, 2)]
}

@dataclass
class TetrisState:
    kind: str
    board: List[List[str | None]] # shape name or None
    falling_shape: str
    falling_pos: Tuple[int, int] # (r, c)
    num_cleared: int

def build_state(rng: random.Random, kind: str) -> TetrisState:
    board = [[None for _ in range(N_COLS)] for _ in range(N_ROWS)]
    
    # Randomly fill bottom rows
    for r in range(N_ROWS - 1, N_ROWS - 5, -1):
        num_blocks = rng.randint(4, 8)
        cols = random.sample(range(N_COLS), num_blocks)
        for c in cols:
            board[r][c] = rng.choice(list(PIECES.keys()))
            
    falling_shape = rng.choice(list(PIECES.keys()))
    falling_c = rng.randint(0, N_COLS - 4)
    falling_r = 1
    
    # Calculate how many lines would be cleared if dropped in current column
    # 1. Find landing row
    coords = PIECES[falling_shape]
    landing_r = falling_r
    while True:
        next_r = landing_r + 1
        blocked = False
        for dr, dc in coords:
            nr, nc = next_r + dr, falling_c + dc
            if nr >= N_ROWS or (nr >= 0 and board[nr][nc] is not None):
                blocked = True
                break
        if blocked:
            break
        landing_r = next_r
        
    # 2. Simulate landing
    temp_board = [row[:] for row in board]
    for dr, dc in coords:
        nr, nc = landing_r + dr, falling_c + dc
        if 0 <= nr < N_ROWS:
            temp_board[nr][nc] = falling_shape
            
    # 3. Count cleared
    num_cleared = 0
    for r in range(N_ROWS):
        if all(temp_board[r][c] is not None for c in range(N_COLS)):
            num_cleared += 1
            
    return TetrisState(kind, board, falling_shape, (falling_r, falling_c), num_cleared)

def solve(state: TetrisState) -> str:
    if state.kind == "identify_shape":
        return state.falling_shape
    elif state.kind == "count_cleared":
        return str(state.num_cleared)
    raise ValueError(state.kind)

def render(state: TetrisState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    # Adjust for N_ROWS x N_COLS
    cell_w = CANVAS // N_COLS
    cell_h = CANVAS // N_ROWS
    
    # Draw grid
    for c in range(N_COLS + 1):
        draw.line((c * cell_w, 0, c * cell_w, CANVAS), fill=GRID, width=1)
    for r in range(N_ROWS + 1):
        draw.line((0, r * cell_h, CANVAS, r * cell_h), fill=GRID, width=1)
        
    # Draw board blocks
    for r in range(N_ROWS):
        for c in range(N_COLS):
            shape = state.board[r][c]
            if shape:
                draw.rectangle((c * cell_w + 2, r * cell_h + 2, (c + 1) * cell_w - 2, (r + 1) * cell_h - 2), fill=COLORS[shape], outline=(0,0,0))
                
    # Draw falling piece
    r0, c0 = state.falling_pos
    coords = PIECES[state.falling_shape]
    color = COLORS[state.falling_shape]
    for dr, dc in coords:
        r, c = r0 + dr, c0 + dc
        draw.rectangle((c * cell_w + 2, r * cell_h + 2, (c + 1) * cell_w - 2, (r + 1) * cell_h - 2), fill=color, outline=HIGHLIGHT, width=2)
        
    img.save(path)

def record(idx: int, seed: int, state: TetrisState, answer: str, media: str) -> Dict:
    if state.kind == "identify_shape":
        q = "<image> This is a Tetris board. A highlighted piece is currently falling. Which tetromino shape is it (I, O, T, S, Z, J, or L)?"
        choices, atype, diff, score = list(PIECES.keys()), "string", "easy", 0.3
    else:
        q = "<image> This is a Tetris board. If the highlighted falling piece drops straight down from its current column, how many horizontal lines will be completely filled and cleared? Answer with a number only."
        choices, atype, diff, score = ["0", "1", "2", "3", "4"], "count", "medium", 0.6
        
    return {
        "id": f"r_tetris_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "tetris_mechanics",
                "reasoning_type": "simulation",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "tetris_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Tetris",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "10x12 Tetris board with partially filled bottom rows and one falling piece.",
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE
            },
            "gt": {
                "answer": answer,
                "answer_text": answer,
                "answer_type": atype,
                "choices": choices,
                "validator": {"kind": "exact_match", "solution": answer}
            },
            "instance": {
                "difficulty": diff,
                "complexity_score": score,
                "reasoning_depth": 1,
                "visual_load": 0.5,
                "tags": ["tetris", "grid", "shapes", "line-clear"],
                "raw_state": {
                    "kind": state.kind,
                    "falling_shape": state.falling_shape,
                    "falling_pos": state.falling_pos,
                    "num_cleared": state.num_cleared
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
        kind = ["identify_shape", "count_cleared"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "tetris_v1.line_clear", "rule": "A horizontal row is cleared when all cells in that row are filled with blocks."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "tetris_v1",
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
            "images": "images/"
        }
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="generated/tetris_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Tetris VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
