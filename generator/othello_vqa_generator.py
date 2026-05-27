#!/usr/bin/env python3
"""Generate deterministic VQA samples for Othello."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

VERSION = "othello_v1.0.0"
SCRIPT_NAME = "othello_vqa_generator.py"
CANVAS = 600
N = 8
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Othello"

BG = (20, 20, 20)
BOARD_COLOR = (30, 150, 60)
GRID_LINE = (20, 100, 40)
BLACK_PIECE = (10, 10, 10)
WHITE_PIECE = (245, 245, 245)
HIGHLIGHT = (255, 200, 50)

@dataclass
class OthelloState:
    kind: str
    board: List[List[str]]  # "B", "W", or " "
    question_cell: Tuple[int, int]
    question_color: str  # "Black" or "White"
    num_flipped: int

def get_flipped(board: List[List[str]], r: int, c: int, color: str) -> List[Tuple[int, int]]:
    if board[r][c] != " ":
        return []
    
    flipped = []
    opp = "W" if color == "B" else "B"
    
    for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
        nr, nc = r + dr, c + dc
        path = []
        while 0 <= nr < N and 0 <= nc < N and board[nr][nc] == opp:
            path.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == color:
            flipped.extend(path)
            
    return flipped

def get_legal_moves(board: List[List[str]], color: str) -> List[Tuple[int, int]]:
    moves = []
    for r in range(N):
        for c in range(N):
            if get_flipped(board, r, c, color):
                moves.append((r, c))
    return moves

def generate_board(rng: random.Random, num_moves: int) -> List[List[str]]:
    board = [[" " for _ in range(N)] for _ in range(N)]
    board[3][3] = "W"
    board[3][4] = "B"
    board[4][3] = "B"
    board[4][4] = "W"
    
    color = "B"
    for _ in range(num_moves):
        moves = get_legal_moves(board, color)
        if not moves:
            color = "W" if color == "B" else "B"
            moves = get_legal_moves(board, color)
            if not moves:
                break
        
        r, c = rng.choice(moves)
        flipped = get_flipped(board, r, c, color)
        board[r][c] = color
        for fr, fc in flipped:
            board[fr][fc] = color
        
        color = "W" if color == "B" else "B"
        
    return board

def build_state(rng: random.Random, kind: str) -> OthelloState:
    board = generate_board(rng, rng.randint(15, 30))
    q_color = rng.choice(["B", "W"])
    q_color_name = "Black" if q_color == "B" else "White"
    
    legal_moves = get_legal_moves(board, q_color)
    empty_cells = [(r, c) for r in range(N) for c in range(N) if board[r][c] == " "]
    
    if kind == "is_legal":
        # 50% chance to pick a legal move, 50% illegal (but empty)
        if legal_moves and (not empty_cells or rng.choice([True, False])):
            q_cell = rng.choice(legal_moves)
        else:
            illegal = [c for c in empty_cells if c not in legal_moves]
            if illegal:
                q_cell = rng.choice(illegal)
            else:
                q_cell = rng.choice(legal_moves) if legal_moves else (0, 0)
    else: # count_flipped
        if legal_moves:
            q_cell = rng.choice(legal_moves)
        else:
            q_cell = rng.choice(empty_cells) if empty_cells else (0, 0)
            
    num_flipped = len(get_flipped(board, q_cell[0], q_cell[1], q_color))
    
    return OthelloState(kind, board, q_cell, q_color_name, num_flipped)

def solve(state: OthelloState) -> str:
    if state.kind == "is_legal":
        return "yes" if state.num_flipped > 0 else "no"
    elif state.kind == "count_flipped":
        return str(state.num_flipped)
    raise ValueError(state.kind)

def render(state: OthelloState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    # Draw board background
    draw.rectangle((0, 0, CANVAS, CANVAS), fill=BOARD_COLOR)
    
    # Draw grid lines
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=GRID_LINE, width=4)
        draw.line((0, p, CANVAS, p), fill=GRID_LINE, width=4)
        
    # Draw dots for standard 8x8 Othello (at 2,2; 2,6; 6,2; 6,6)
    for r in [2, 6]:
        for c in [2, 6]:
            cx, cy = c * CELL, r * CELL
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=GRID_LINE)
            
    # Draw pieces
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            
            if state.board[r][c] != " ":
                color = BLACK_PIECE if state.board[r][c] == "B" else WHITE_PIECE
                draw.ellipse((x0 + 8, y0 + 8, x1 - 8, y1 - 8), fill=color)
                
            if (r, c) == state.question_cell:
                draw.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), outline=HIGHLIGHT, width=4)
                
    img.save(path)

def record(idx: int, seed: int, state: OthelloState, answer: str, media: str) -> Dict:
    if state.kind == "is_legal":
        q = f"<image> This is an Othello board. The yellow-outlined square indicates a potential move for {state.question_color}. Is this a legal move? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "easy", 0.4
    else:
        opp_color = "White" if state.question_color == "Black" else "Black"
        q = f"<image> This is an Othello board. If {state.question_color} places a piece on the yellow-outlined square, how many {opp_color} pieces will be flipped? Answer with a number only."
        choices, atype, diff, score = [str(i) for i in range(15)], "count", "medium", 0.7
        
    return {
        "id": f"r_othello_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "othello_mechanics",
                "reasoning_type": "game_rule_planning",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "othello_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Othello",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "8x8 Othello board after a random number of legal moves.",
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
                "visual_load": 0.8,
                "tags": ["othello", "grid", "flipping", "legal-move"],
                "raw_state": {
                    "kind": state.kind,
                    "board": state.board,
                    "question_cell": list(state.question_cell),
                    "question_color": state.question_color,
                    "num_flipped": state.num_flipped
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
        kind = ["is_legal", "count_flipped"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "othello_v1.legal_move", "rule": "A legal move must bracket at least one opponent disc between the newly placed disc and an existing disc of the player's color, in a straight line."},
        {"id": "othello_v1.flip", "rule": "All bracketed opponent discs in a straight line are flipped to the player's color."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "othello_v1",
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
            "images": "images/"
        }
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="generated/othello_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Othello VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
