#!/usr/bin/env python3
"""Generate deterministic VQA samples for Tic-tac-toe."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "tictactoe_v1.0.0"
SCRIPT_NAME = "tictactoe_vqa_generator.py"
CANVAS = 600
N = 3
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Tic-tac-toe"

BG = (250, 250, 250)
GRID = (50, 50, 50)
X_COLOR = (220, 50, 50)
O_COLOR = (50, 100, 220)
HIGHLIGHT = (255, 200, 50)

@dataclass
class TicTacToeState:
    kind: str
    board: List[List[str]] # "X", "O", or " "
    current_player: str
    winner: str | None
    winning_move: Tuple[int, int] | None

def check_winner(board: List[List[str]]) -> str | None:
    # Rows
    for r in range(3):
        if board[r][0] != " " and board[r][0] == board[r][1] == board[r][2]: return board[r][0]
    # Cols
    for c in range(3):
        if board[0][c] != " " and board[0][c] == board[1][c] == board[2][c]: return board[0][c]
    # Diagonals
    if board[0][0] != " " and board[0][0] == board[1][1] == board[2][2]: return board[0][0]
    if board[0][2] != " " and board[0][2] == board[1][1] == board[2][0]: return board[0][2]
    return None

def find_winning_move(board: List[List[str]], player: str) -> Tuple[int, int] | None:
    for r in range(3):
        for c in range(3):
            if board[r][c] == " ":
                board[r][c] = player
                if check_winner(board) == player:
                    board[r][c] = " " # undo
                    return (r, c)
                board[r][c] = " "
    return None

def build_state(rng: random.Random, kind: str) -> TicTacToeState:
    board = [[" " for _ in range(3)] for _ in range(3)]
    
    # Randomly fill board
    num_moves = rng.randint(4, 7)
    player = "X"
    for _ in range(num_moves):
        empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] == " "]
        if not empty: break
        r, c = rng.choice(empty)
        board[r][c] = player
        if check_winner(board): break
        player = "O" if player == "X" else "X"
        
    winner = check_winner(board)
    winning_move = None
    
    if kind == "winning_move":
        # Force a winning move scenario
        player = "X" if rng.choice([True, False]) else "O"
        # Clear board and build scenario
        board = [[" " for _ in range(3)] for _ in range(3)]
        # Place 2 of player's marks in a line
        line = rng.choice(["row", "col", "diag"])
        idx = rng.randint(0, 2)
        if line == "row":
            board[idx][0] = player
            board[idx][1] = player
            winning_move = (idx, 2)
        elif line == "col":
            board[0][idx] = player
            board[1][idx] = player
            winning_move = (2, idx)
        else:
            board[0][0] = player
            board[1][1] = player
            winning_move = (2, 2)
            
        # Add some random opponent marks
        opp = "O" if player == "X" else "X"
        empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] == " " and (r, c) != winning_move]
        for _ in range(rng.randint(2, 4)):
            if not empty: break
            r, c = rng.choice(empty)
            board[r][c] = opp
            empty.remove((r, c))
            
    return TicTacToeState(kind, board, player, winner, winning_move)

def solve(state: TicTacToeState) -> str:
    if state.kind == "who_won":
        return state.winner if state.winner else "none"
    elif state.kind == "winning_move":
        return f"{state.winning_move[0]},{state.winning_move[1]}" if state.winning_move else "none"
    raise ValueError(state.kind)

def render(state: TicTacToeState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    # Grid
    for i in range(1, 3):
        draw.line((i * CELL, 0, i * CELL, CANVAS), fill=GRID, width=8)
        draw.line((0, i * CELL, CANVAS, i * CELL), fill=GRID, width=8)
        
    for r in range(3):
        for c in range(3):
            x0, y0 = c * CELL + 20, r * CELL + 20
            x1, y1 = (c + 1) * CELL - 20, (r + 1) * CELL - 20
            
            if state.board[r][c] == "X":
                draw.line((x0, y0, x1, y1), fill=X_COLOR, width=15)
                draw.line((x1, y0, x0, y1), fill=X_COLOR, width=15)
            elif state.board[r][c] == "O":
                draw.ellipse((x0, y0, x1, y1), outline=O_COLOR, width=15)
                
    img.save(path)

def record(idx: int, seed: int, state: TicTacToeState, answer: str, media: str) -> Dict:
    if state.kind == "who_won":
        q = "<image> This is a Tic-tac-toe board. Has X or O won the game? Answer with X, O, or none."
        atype, diff, score = "string", "easy", 0.2
    else:
        q = f"<image> This is a Tic-tac-toe board. Coordinates are (row, column) from 0 to 2. At which coordinate should {state.current_player} play to win immediately? Answer in r,c format."
        atype, diff, score = "string", "medium", 0.5
        
    return {
        "id": f"r_tictactoe_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": [], "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "tictactoe_logic",
                "reasoning_type": "deductive",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "tictactoe_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Tic-tac-toe",
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
                "visual_load": 0.3,
                "tags": ["tictactoe", "grid", "win-condition"],
                "raw_state": {
                    "board": state.board,
                    "current_player": state.current_player,
                    "winner": state.winner,
                    "winning_move": state.winning_move
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
        kind = ["who_won", "winning_move"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "tictactoe_v1.win", "rule": "Three of the same marks in a row, column, or diagonal wins."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "tictactoe_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "low", "reasoning_max": "low", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/tictactoe_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Tic-tac-toe VQA records to {a.out_dir}")

if __name__ == "__main__": main()
