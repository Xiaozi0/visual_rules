#!/usr/bin/env python3
"""Generate deterministic VQA samples for Connect Four."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "connect_four_v1.0.0"
SCRIPT_NAME = "connect_four_vqa_generator.py"
CANVAS = 600
COLS = 7
ROWS = 6
CELL = CANVAS // COLS
RULE_SOURCE = "original/批次 5-0521.md:Connect Four"

BG = (20, 20, 20)
BOARD = (40, 100, 220)
EMPTY = (30, 30, 30)
RED = (220, 50, 50)
YELLOW = (220, 200, 50)
HIGHLIGHT = (255, 255, 255)

@dataclass
class ConnectFourState:
    kind: str
    board: List[List[str]]  # "R", "Y", or " "
    current_player: str
    question_col: int | None
    answer_col: int | None
    win: bool

def drop_piece(board: List[List[str]], col: int, color: str) -> int:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == " ":
            board[r][col] = color
            return r
    return -1

def check_win(board: List[List[str]], color: str) -> bool:
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == color:
                # Horizontal
                if c + 3 < COLS and all(board[r][c+i] == color for i in range(4)): return True
                # Vertical
                if r + 3 < ROWS and all(board[r+i][c] == color for i in range(4)): return True
                # Diagonal /
                if r - 3 >= 0 and c + 3 < COLS and all(board[r-i][c+i] == color for i in range(4)): return True
                # Diagonal \
                if r + 3 < ROWS and c + 3 < COLS and all(board[r+i][c+i] == color for i in range(4)): return True
    return False

def get_winning_moves(board: List[List[str]], color: str) -> List[int]:
    wins = []
    for c in range(COLS):
        if board[0][c] == " ":
            r = drop_piece(board, c, color)
            if check_win(board, color):
                wins.append(c)
            board[r][c] = " "
    return wins

def build_state(rng: random.Random, kind: str) -> ConnectFourState:
    board = [[" " for _ in range(COLS)] for _ in range(ROWS)]
    
    # Simulate a game
    color = "R"
    for _ in range(rng.randint(15, 25)):
        valid_cols = [c for c in range(COLS) if board[0][c] == " "]
        if not valid_cols: break
        
        # Don't make a move that wins immediately unless we want to end
        c = rng.choice(valid_cols)
        r = drop_piece(board, c, color)
        if check_win(board, color):
            board[r][c] = " " # undo
            break
        color = "Y" if color == "R" else "R"

    q_col = None
    ans_col = None
    win = False
    
    if kind == "will_win":
        color = rng.choice(["R", "Y"])
        valid_cols = [c for c in range(COLS) if board[0][c] == " "]
        wins = get_winning_moves(board, color)
        
        if wins and rng.choice([True, False]):
            q_col = rng.choice(wins)
            win = True
        elif valid_cols:
            non_wins = [c for c in valid_cols if c not in wins]
            if non_wins:
                q_col = rng.choice(non_wins)
            else:
                q_col = rng.choice(valid_cols)
                win = q_col in wins
        else:
            q_col = 0
            
    elif kind == "block_win":
        color = rng.choice(["R", "Y"])
        opp = "Y" if color == "R" else "R"
        
        # We need to guarantee opponent has a winning move
        # Let's just find if opp has a win. If not, artificially create one.
        opp_wins = get_winning_moves(board, opp)
        if not opp_wins:
            valid_cols = [c for c in range(COLS) if board[0][c] == " "]
            if valid_cols:
                # Force a win
                c = rng.choice(valid_cols)
                board[ROWS-1][c] = opp
                board[ROWS-2][c] = opp
                board[ROWS-3][c] = opp
                if board[ROWS-4][c] == " ":
                    opp_wins = [c]
        
        if opp_wins:
            ans_col = opp_wins[0]
        else:
            ans_col = 0 # fallback
            
    return ConnectFourState(kind, board, color, q_col, ans_col, win)

def solve(state: ConnectFourState) -> str:
    if state.kind == "will_win":
        return "yes" if state.win else "no"
    elif state.kind == "block_win":
        return str(state.answer_col)
    raise ValueError(state.kind)

def render(state: ConnectFourState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    # Adjust CELL height to fit 6 rows, width to fit 7 cols
    cell_w = CANVAS // COLS
    cell_h = CANVAS // ROWS
    
    draw.rectangle((0, 0, CANVAS, CANVAS), fill=BOARD)
    
    # Draw slots
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = c * cell_w, r * cell_h
            x1, y1 = (c + 1) * cell_w, (r + 1) * cell_h
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            radius = min(cell_w, cell_h) // 2 - 8
            
            val = state.board[r][c]
            color = EMPTY
            if val == "R": color = RED
            if val == "Y": color = YELLOW
            
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)
            
            # Highlight column
            if state.kind == "will_win" and state.question_col == c:
                draw.rectangle((c*cell_w, 0, (c+1)*cell_w, CANVAS), outline=HIGHLIGHT, width=4)

    # Draw column numbers
    font = ImageFont.load_default()
    for c in range(COLS):
        x = c * cell_w + cell_w // 2 - 4
        y = 10
        draw.text((x, y), str(c), fill=HIGHLIGHT, font=font)
                
    img.save(path)

def record(idx: int, seed: int, state: ConnectFourState, answer: str, media: str) -> Dict:
    player_name = "Red" if state.current_player == "R" else "Yellow"
    
    if state.kind == "will_win":
        q = f"<image> This is a Connect Four board. The columns are numbered 0 to 6 from left to right. Column {state.question_col} is highlighted. If {player_name} drops a disc into this column, will {player_name} immediately win the game? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "easy", 0.4
    else:
        opp = "Yellow" if player_name == "Red" else "Red"
        q = f"<image> This is a Connect Four board. The columns are numbered 0 to 6 from left to right. {opp} threatens to win on their next turn. Which column must {player_name} drop a disc into to block {opp} from winning? Answer with the column number only."
        choices, atype, diff, score = [str(i) for i in range(7)], "string", "medium", 0.6
        
    return {
        "id": f"r_connect_four_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "connect_four_mechanics",
                "reasoning_type": "game_rule_planning",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "connect_four_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Connect Four",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "7x6 Connect Four board.",
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
                "tags": ["connect-four", "grid", "gravity", "win-condition"],
                "raw_state": {
                    "kind": state.kind,
                    "board": state.board,
                    "current_player": state.current_player,
                    "question_col": state.question_col,
                    "answer_col": state.answer_col,
                    "win": state.win
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
        kind = ["will_win", "block_win"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "connect_four_v1.gravity", "rule": "Discs dropped into a column fall to the lowest available empty space."},
        {"id": "connect_four_v1.win", "rule": "A player wins by aligning four of their discs horizontally, vertically, or diagonally."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "connect_four_v1",
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
    p.add_argument("--out-dir", default="generated/connect_four_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Connect Four VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
