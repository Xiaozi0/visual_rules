#!/usr/bin/env python3
"""Generate deterministic VQA samples for Flood It."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

from PIL import Image, ImageDraw

VERSION = "flood_it_v1.0.0"
SCRIPT_NAME = "flood_it_vqa_generator.py"
CANVAS = 600
N = 14
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Flood It"

COLORS = {
    "red": (220, 50, 50),
    "green": (50, 200, 50),
    "blue": (50, 100, 220),
    "yellow": (230, 200, 50),
    "purple": (150, 50, 200),
    "orange": (230, 130, 40)
}
COLOR_NAMES = list(COLORS.keys())
BG = (20, 20, 20)
BORDER = (255, 255, 255)

@dataclass
class FloodItState:
    kind: str
    board: List[List[str]]
    connected: Set[Tuple[int, int]]
    question_color: str | None
    added_blocks: int
    best_color: str | None

def get_connected(board: List[List[str]]) -> Set[Tuple[int, int]]:
    color = board[0][0]
    visited = set()
    stack = [(0, 0)]
    while stack:
        r, c = stack.pop()
        if (r, c) not in visited and board[r][c] == color:
            visited.add((r, c))
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    stack.append((nr, nc))
    return visited

def get_added(board: List[List[str]], connected: Set[Tuple[int, int]], new_color: str) -> int:
    added = set()
    stack = []
    
    # Find all adjacent blocks of the new color
    for r, c in connected:
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in connected and board[nr][nc] == new_color:
                stack.append((nr, nc))
                
    # Flood from those adjacent blocks
    while stack:
        r, c = stack.pop()
        if (r, c) not in added and board[r][c] == new_color:
            added.add((r, c))
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in connected:
                    stack.append((nr, nc))
                    
    return len(added)

def simulate_steps(rng: random.Random, board: List[List[str]], num_steps: int) -> None:
    for _ in range(num_steps):
        conn = get_connected(board)
        # pick a color that is adjacent
        adj_colors = set()
        for r, c in conn:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in conn:
                    adj_colors.add(board[nr][nc])
        if adj_colors:
            c = rng.choice(list(adj_colors))
            for r, cc in conn:
                board[r][cc] = c

def build_state(rng: random.Random, kind: str) -> FloodItState:
    board = [[rng.choice(COLOR_NAMES) for _ in range(N)] for _ in range(N)]
    simulate_steps(rng, board, rng.randint(5, 15))
    
    connected = get_connected(board)
    current_color = board[0][0]
    
    adj_colors = set()
    for r, c in connected:
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in connected:
                adj_colors.add(board[nr][nc])
                
    q_color = None
    added_blocks = 0
    best_color = None
    
    if adj_colors:
        best_count = -1
        for c in adj_colors:
            count = get_added(board, connected, c)
            if count > best_count:
                best_count = count
                best_color = c
                
        if kind == "count_added":
            q_color = rng.choice(list(adj_colors))
            added_blocks = get_added(board, connected, q_color)
            
    return FloodItState(kind, board, connected, q_color, added_blocks, best_color)

def solve(state: FloodItState) -> str:
    if state.kind == "count_added":
        return str(state.added_blocks)
    elif state.kind == "best_color":
        return state.best_color if state.best_color else "none"
    raise ValueError(state.kind)

def render(state: FloodItState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            
            color = COLORS[state.board[r][c]]
            draw.rectangle((x0, y0, x1, y1), fill=color)
            
            # Draw borders between connected and non-connected
            if (r, c) in state.connected:
                for dr, dc, edge in [(-1,0, "top"), (1,0, "bottom"), (0,-1, "left"), (0,1, "right")]:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < N and 0 <= nc < N) or (nr, nc) not in state.connected:
                        if edge == "top":
                            draw.line((x0, y0, x1, y0), fill=BORDER, width=4)
                        elif edge == "bottom":
                            draw.line((x0, y1, x1, y1), fill=BORDER, width=4)
                        elif edge == "left":
                            draw.line((x0, y0, x0, y1), fill=BORDER, width=4)
                        elif edge == "right":
                            draw.line((x1, y0, x1, y1), fill=BORDER, width=4)

    img.save(path)

def record(idx: int, seed: int, state: FloodItState, answer: str, media: str) -> Dict:
    if state.kind == "count_added":
        q = f"<image> This is a Flood It board. The top-left connected region is enclosed by a white border. If the player chooses {state.question_color}, how many new blocks will be added to the connected region? Answer with a number only."
        choices, atype, diff, score = [str(i) for i in range(20)], "count", "medium", 0.5
    else:
        q = "<image> This is a Flood It board. The top-left connected region is enclosed by a white border. Which color choice would add the most new blocks to the connected region? Answer with the color name only."
        choices, atype, diff, score = COLOR_NAMES, "string", "hard", 0.8
        
    return {
        "id": f"r_flood_it_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "flood_it_planning",
                "reasoning_type": "algorithmic",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "flood_it_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Flood It",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": f"14x14 Flood It board after {rng.randint(5, 15) if 'rng' in locals() else 'some'} random moves.",
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
                "reasoning_depth": 2,
                "visual_load": 1.0,
                "tags": ["flood-it", "grid", "connected-components", "planning"],
                "raw_state": {
                    "kind": state.kind,
                    "board": state.board,
                    "connected": list(state.connected),
                    "question_color": state.question_color,
                    "added_blocks": state.added_blocks,
                    "best_color": state.best_color
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
    # Give the rng object to a global scope or avoid using it in `record` provenance
    global global_rng
    global_rng = rng
    records = []
    
    for idx in range(count):
        s = rng.randint(10_000_000, 999_999_999)
        kind = ["count_added", "best_color"][idx % 2]
        state = build_state(random.Random(s), kind)
        if not state.best_color: # Handle edge case where board is solved or no moves
            continue
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "flood_it_v1.flood", "rule": "Choosing a color changes the entire top-left connected region to that color and absorbs any adjacent blocks of the newly chosen color."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "flood_it_v1",
        "version": VERSION,
        "generator": SCRIPT_NAME,
        "count": len(records),
        "seed": seed,
        "build_complexity": "medium",
        "reasoning_max": "high",
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
    p.add_argument("--out-dir", default="generated/flood_it_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Flood It VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
