#!/usr/bin/env python3
"""Generate deterministic VQA samples for Pipe Dream."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Set

from PIL import Image, ImageDraw

VERSION = "pipe_dream_v1.0.0"
SCRIPT_NAME = "pipe_dream_vqa_generator.py"
CANVAS = 600
N = 10
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Pipe Dream"

BG = (30, 40, 50)
PIPE_COLOR = (180, 200, 220)
GRID = (50, 60, 70)
START_COLOR = (50, 220, 50)
END_COLOR = (220, 50, 50)
HIGHLIGHT = (255, 200, 50)

# Maps piece type to its open ports: (dr, dc)
PIPES = {
    "straight_h": {str((0, -1)), str((0, 1))},
    "straight_v": {str((-1, 0)), str((1, 0))},
    "corner_ul": {str((0, 1)), str((1, 0))},
    "corner_ur": {str((0, -1)), str((1, 0))},
    "corner_dl": {str((0, 1)), str((-1, 0))},
    "corner_dr": {str((0, -1)), str((-1, 0))},
    "start_u": {str((-1, 0))},
    "start_d": {str((1, 0))},
    "start_l": {str((0, -1))},
    "start_r": {str((0, 1))},
    "end_u": {str((-1, 0))},
    "end_d": {str((1, 0))},
    "end_l": {str((0, -1))},
    "end_r": {str((0, 1))}
}

PIPE_TYPES = ["straight_h", "straight_v", "corner_ul", "corner_ur", "corner_dl", "corner_dr"]

@dataclass
class PipeDreamState:
    kind: str
    board: List[List[str]]
    start_pos: Tuple[int, int]
    end_pos: Tuple[int, int]
    question_pos: Tuple[int, int] | None
    will_reach: bool
    is_connected: bool

def get_opposite(port_str: str) -> str:
    r, c = eval(port_str)
    return str((-r, -c))

def trace_flow(board: List[List[str]], start_pos: Tuple[int, int]) -> Set[Tuple[int, int]]:
    visited = set()
    stack = [start_pos]
    
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
            
        visited.add((r, c))
        piece = board[r][c]
        if piece == "empty": continue
        
        ports = PIPES[piece]
        for p in ports:
            dr, dc = eval(p)
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                npiece = board[nr][nc]
                if npiece != "empty":
                    nports = PIPES[npiece]
                    if get_opposite(p) in nports:
                        stack.append((nr, nc))
    return visited

def generate_random_board(rng: random.Random) -> List[List[str]]:
    board = [["empty" for _ in range(N)] for _ in range(N)]
    
    # 1. Pick start and end
    sr, sc = rng.randint(0, N-1), rng.randint(0, N-1)
    er, ec = rng.randint(0, N-1), rng.randint(0, N-1)
    while (sr, sc) == (er, ec):
        er, ec = rng.randint(0, N-1), rng.randint(0, N-1)
        
    s_dirs = []
    if sr > 0: s_dirs.append("u")
    if sr < N-1: s_dirs.append("d")
    if sc > 0: s_dirs.append("l")
    if sc < N-1: s_dirs.append("r")
    board[sr][sc] = "start_" + rng.choice(s_dirs)
    
    e_dirs = []
    if er > 0: e_dirs.append("u")
    if er < N-1: e_dirs.append("d")
    if ec > 0: e_dirs.append("l")
    if ec < N-1: e_dirs.append("r")
    board[er][ec] = "end_" + rng.choice(e_dirs)
    
    # Fill the rest with random pipes
    for r in range(N):
        for c in range(N):
            if board[r][c] == "empty":
                board[r][c] = rng.choice(PIPE_TYPES)
                
    return board

def build_state(rng: random.Random, kind: str) -> PipeDreamState:
    board = generate_random_board(rng)
    
    sr, sc = -1, -1
    er, ec = -1, -1
    for r in range(N):
        for c in range(N):
            if board[r][c].startswith("start_"):
                sr, sc = r, c
            elif board[r][c].startswith("end_"):
                er, ec = r, c
                
    # To make questions interesting, let's artificially build a path sometimes
    if rng.choice([True, False]):
        # Very simple hack: if we want to ensure path, we might need a solver.
        # Given small grid, random is unlikely to connect.
        # Let's just use whatever random gives (usually False) but sometimes we can
        # just do a random walk from start and modify pipes to connect.
        curr_r, curr_c = sr, sc
        path_visited = {(sr, sc)}
        # find outgoing port from start
        port = list(PIPES[board[sr][sc]])[0]
        dr, dc = eval(port)
        nr, nc = sr + dr, sc + dc
        
        while 0 <= nr < N and 0 <= nc < N and (nr, nc) != (er, ec) and (nr, nc) not in path_visited:
            path_visited.add((nr, nc))
            in_port = get_opposite(port)
            # pick an out port
            possible_out_dirs = [d for d in [(-1,0), (1,0), (0,-1), (0,1)] if str(d) != in_port]
            out_port = str(rng.choice(possible_out_dirs))
            
            # find a pipe that matches in_port and out_port
            for ptype in PIPE_TYPES:
                if in_port in PIPES[ptype] and out_port in PIPES[ptype]:
                    board[nr][nc] = ptype
                    break
            
            dr, dc = eval(out_port)
            curr_r, curr_c = nr, nc
            port = out_port
            nr, nc = curr_r + dr, curr_c + dc
            
        if (nr, nc) == (er, ec):
            # Try to connect to end
            end_in_port = get_opposite(port)
            if end_in_port in PIPES[board[er][ec]]:
                pass # Already connected
            else:
                # Modify end pipe to match
                dr, dc = eval(end_in_port)
                if dr == -1: board[er][ec] = "end_u"
                elif dr == 1: board[er][ec] = "end_d"
                elif dc == -1: board[er][ec] = "end_l"
                elif dc == 1: board[er][ec] = "end_r"
                
    # Evaluate
    connected_set = trace_flow(board, (sr, sc))
    will_reach = (er, ec) in connected_set
    
    q_pos = None
    is_connected = False
    
    if kind == "is_connected":
        # Don't ask about start or end
        candidates = [(r, c) for r in range(N) for c in range(N) if (r, c) != (sr, sc) and (r, c) != (er, ec)]
        if candidates:
            # 50% chance connected, 50% chance not connected (if possible)
            conn_cands = [c for c in candidates if c in connected_set]
            not_conn_cands = [c for c in candidates if c not in connected_set]
            
            if conn_cands and (not not_conn_cands or rng.choice([True, False])):
                q_pos = rng.choice(conn_cands)
                is_connected = True
            elif not_conn_cands:
                q_pos = rng.choice(not_conn_cands)
                is_connected = False
            else:
                q_pos = rng.choice(candidates)
                is_connected = q_pos in connected_set
                
    return PipeDreamState(kind, board, (sr, sc), (er, ec), q_pos, will_reach, is_connected)

def solve(state: PipeDreamState) -> str:
    if state.kind == "will_reach_end":
        return "yes" if state.will_reach else "no"
    elif state.kind == "is_connected":
        return "yes" if state.is_connected else "no"
    raise ValueError(state.kind)

def render(state: PipeDreamState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=GRID, width=1)
        draw.line((0, p, CANVAS, p), fill=GRID, width=1)
        
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            
            ptype = state.board[r][c]
            if ptype == "empty": continue
            
            color = PIPE_COLOR
            if ptype.startswith("start_"): color = START_COLOR
            if ptype.startswith("end_"): color = END_COLOR
            
            # Draw center joint
            draw.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=color)
            
            # Draw ports
            for port in PIPES[ptype]:
                dr, dc = eval(port)
                if dr == -1: draw.rectangle((cx - 8, y0, cx + 8, cy), fill=color)
                if dr == 1: draw.rectangle((cx - 8, cy, cx + 8, y1), fill=color)
                if dc == -1: draw.rectangle((x0, cy - 8, cx, cy + 8), fill=color)
                if dc == 1: draw.rectangle((cx, cy - 8, x1, cy + 8), fill=color)
                
            if state.kind == "is_connected" and state.question_pos == (r, c):
                draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=HIGHLIGHT, width=4)
                
    img.save(path)

def record(idx: int, seed: int, state: PipeDreamState, answer: str, media: str) -> Dict:
    if state.kind == "will_reach_end":
        q = "<image> This is a Pipe Dream board. The green pipe is the Start and the red pipe is the End. Will the water flowing from the Start successfully reach the End through the current pipe configuration? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "medium", 0.6
    else:
        q = "<image> This is a Pipe Dream board. The green pipe is the Start. Is the yellow-outlined pipe piece connected to the Start network (i.e. will water flow reach it)? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "medium", 0.5
        
    return {
        "id": f"r_pipe_dream_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "pipe_dream_mechanics",
                "reasoning_type": "algorithmic",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "pipe_dream_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Pipe Dream",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "10x10 Pipe Dream board with random pipes and a start/end pair.",
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
                "tags": ["pipe-dream", "grid", "pathfinding", "connectivity"],
                "raw_state": {
                    "kind": state.kind,
                    "board": state.board,
                    "start_pos": list(state.start_pos),
                    "end_pos": list(state.end_pos),
                    "question_pos": list(state.question_pos) if state.question_pos else None,
                    "will_reach": state.will_reach,
                    "is_connected": state.is_connected
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
        kind = ["will_reach_end", "is_connected"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "pipe_dream_v1.connectivity", "rule": "Two pipes are connected if their adjacent ports face each other. Water flows from the Start through all connected pipes."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "pipe_dream_v1",
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
    p.add_argument("--out-dir", default="generated/pipe_dream_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Pipe Dream VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
