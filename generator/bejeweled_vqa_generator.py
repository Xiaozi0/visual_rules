#!/usr/bin/env python3
"""Generate deterministic VQA samples for Bejeweled."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

from PIL import Image, ImageDraw

VERSION = "bejeweled_v1.0.0"
SCRIPT_NAME = "bejeweled_vqa_generator.py"
CANVAS = 600
N = 8
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Bejeweled"

# Colors for gems
COLORS = {
    "red": (220, 50, 50),
    "green": (50, 200, 50),
    "blue": (50, 100, 220),
    "yellow": (230, 200, 50),
    "purple": (150, 50, 200),
    "orange": (230, 130, 40),
    "white": (240, 240, 240)
}
COLOR_NAMES = list(COLORS.keys())
BG = (30, 30, 40)
HIGHLIGHT = (255, 255, 255)

@dataclass
class BejeweledState:
    kind: str
    board: List[List[str]]
    question_r: int
    question_c: int
    swap_dir: str # "up", "down", "left", "right"
    is_valid: bool
    num_eliminated: int

def get_matches(board: List[List[str]]) -> Set[Tuple[int, int]]:
    matches = set()
    
    # Horizontal matches
    for r in range(N):
        for c in range(N - 2):
            if board[r][c] == board[r][c+1] == board[r][c+2]:
                matches.add((r, c))
                matches.add((r, c+1))
                matches.add((r, c+2))
                # Check for 4 or 5
                if c + 3 < N and board[r][c] == board[r][c+3]:
                    matches.add((r, c+3))
                    if c + 4 < N and board[r][c] == board[r][c+4]:
                        matches.add((r, c+4))
                        
    # Vertical matches
    for c in range(N):
        for r in range(N - 2):
            if board[r][c] == board[r+1][c] == board[r+2][c]:
                matches.add((r, c))
                matches.add((r+1, c))
                matches.add((r+2, c))
                if r + 3 < N and board[r][c] == board[r+3][c]:
                    matches.add((r+3, c))
                    if r + 4 < N and board[r][c] == board[r+4][c]:
                        matches.add((r+4, c))
                        
    return matches

def generate_board(rng: random.Random) -> List[List[str]]:
    board = [["" for _ in range(N)] for _ in range(N)]
    for r in range(N):
        for c in range(N):
            available = list(COLOR_NAMES)
            # prevent 3 in a row initially
            if c >= 2 and board[r][c-1] == board[r][c-2]:
                if board[r][c-1] in available:
                    available.remove(board[r][c-1])
            if r >= 2 and board[r-1][c] == board[r-2][c]:
                if board[r-1][c] in available:
                    available.remove(board[r-1][c])
            board[r][c] = rng.choice(available)
    return board

def build_state(rng: random.Random, kind: str) -> BejeweledState:
    board = generate_board(rng)
    
    # Find all possible valid swaps
    valid_swaps = []
    invalid_swaps = []
    
    for r in range(N):
        for c in range(N):
            for dr, dc, dir_name in [(-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    # try swap
                    board[r][c], board[nr][nc] = board[nr][nc], board[r][c]
                    matches = get_matches(board)
                    board[r][c], board[nr][nc] = board[nr][nc], board[r][c] # undo
                    
                    if matches:
                        valid_swaps.append((r, c, dir_name, len(matches)))
                    else:
                        invalid_swaps.append((r, c, dir_name, 0))
                        
    if kind == "is_valid":
        if valid_swaps and (not invalid_swaps or rng.choice([True, False])):
            r, c, d, count = rng.choice(valid_swaps)
            return BejeweledState(kind, board, r, c, d, True, count)
        else:
            r, c, d, count = rng.choice(invalid_swaps)
            return BejeweledState(kind, board, r, c, d, False, count)
    else: # count_eliminated
        # force a valid swap
        r, c, d, count = rng.choice(valid_swaps)
        return BejeweledState(kind, board, r, c, d, True, count)

def solve(state: BejeweledState) -> str:
    if state.kind == "is_valid":
        return "yes" if state.is_valid else "no"
    elif state.kind == "count_eliminated":
        return str(state.num_eliminated)
    raise ValueError(state.kind)

def render(state: BejeweledState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=(50, 50, 60), width=2)
        draw.line((0, p, CANVAS, p), fill=(50, 50, 60), width=2)
        
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            
            color = COLORS[state.board[r][c]]
            # Draw diamond shape
            draw.polygon([(cx, y0 + 10), (x1 - 10, cy), (cx, y1 - 10), (x0 + 10, cy)], fill=color)
            
            if r == state.question_r and c == state.question_c:
                draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=HIGHLIGHT, width=4)
                
                # Draw arrow
                dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[state.swap_dir]
                end_x = cx + dc * 35
                end_y = cy + dr * 35
                draw.line((cx, cy, end_x, end_y), fill=HIGHLIGHT, width=6)
                draw.ellipse((end_x - 4, end_y - 4, end_x + 4, end_y + 4), fill=HIGHLIGHT)
                
    img.save(path)

def record(idx: int, seed: int, state: BejeweledState, answer: str, media: str) -> Dict:
    if state.kind == "is_valid":
        q = f"<image> This is a Bejeweled board. The yellow-outlined gem has an arrow pointing {state.swap_dir}. If the player swaps this gem with the adjacent gem in the direction of the arrow, will it result in a valid match of 3 or more gems? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "easy", 0.4
    else:
        q = f"<image> This is a Bejeweled board. The yellow-outlined gem has an arrow pointing {state.swap_dir}. If the player swaps this gem with the adjacent gem in the direction of the arrow, how many gems will be matched and eliminated? Answer with a number only."
        choices, atype, diff, score = [str(i) for i in range(10)], "count", "medium", 0.6
        
    return {
        "id": f"r_bejeweled_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "bejeweled_mechanics",
                "reasoning_type": "algorithmic",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "bejeweled_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Bejeweled",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "8x8 Bejeweled board with no initial matches.",
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
                "visual_load": 1.0,
                "tags": ["bejeweled", "grid", "match-3"],
                "raw_state": {
                    "kind": state.kind,
                    "board": state.board,
                    "question_r": state.question_r,
                    "question_c": state.question_c,
                    "swap_dir": state.swap_dir,
                    "is_valid": state.is_valid,
                    "num_eliminated": state.num_eliminated
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
        kind = ["is_valid", "count_eliminated"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "bejeweled_v1.swap", "rule": "A valid move swaps two adjacent gems to form a straight line of 3 or more identically colored gems."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "bejeweled_v1",
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
    p.add_argument("--out-dir", default="generated/bejeweled_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Bejeweled VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
