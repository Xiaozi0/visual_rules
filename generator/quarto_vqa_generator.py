#!/usr/bin/env python3
"""Generate deterministic VQA samples for Quarto."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

VERSION = "quarto_v1.0.0"
SCRIPT_NAME = "quarto_vqa_generator.py"
CANVAS = 600
N = 4
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Quarto"

COLORS = {'black': (20, 20, 20), 'white': (240, 240, 240)}
ATTRS = ['tall', 'round', 'hollow', 'white']

def build_state(rng: random.Random) -> Tuple[List[List[int | None]], int, str | None]:
    board = [[None for _ in range(N)] for _ in range(N)]
    used = set()
    for _ in range(rng.randint(6, 12)):
        r, c = rng.randint(0, 3), rng.randint(0, 3)
        if board[r][c] is None:
            piece = rng.randint(0, 15)
            if piece not in used:
                board[r][c] = piece
                used.add(piece)
    q_row = rng.randint(0, 3)
    # Force a win in this row sometimes
    if rng.choice([True, False]):
        attr_idx = rng.randint(0, 3)
        val = rng.randint(0, 1)
        for c in range(4):
            # find a piece that matches
            for p in range(16):
                if p not in used and ((p >> attr_idx) & 1) == val:
                    board[q_row][c] = p
                    used.add(p)
                    break
    row_pieces = [board[q_row][c] for c in range(4)]
    shared = None
    if all(p is not None for p in row_pieces):
        for i in range(4):
            bits = [(p >> i) & 1 for p in row_pieces]
            if len(set(bits)) == 1:
                shared = ATTRS[i]
                break
    return board, q_row, shared

def render(board, q_row, path):
    img = Image.new('RGB', (CANVAS, CANVAS), (180, 160, 140))
    draw = ImageDraw.Draw(img)
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            draw.ellipse((x0+10, y0+10, x1-10, y1-10), fill=(140, 120, 100))
            p = board[r][c]
            if p is not None:
                tall = (p >> 0) & 1
                round_p = (p >> 1) & 1
                hollow = (p >> 2) & 1
                white = (p >> 3) & 1
                color = COLORS['white' if white else 'black']
                cx, cy = (x0+x1)//2, (y0+y1)//2
                size = 50 if tall else 30
                if round_p:
                    draw.ellipse((cx-size, cy-size, cx+size, cy+size), fill=color, outline=(0,0,0))
                    if hollow: draw.ellipse((cx-size+10, cy-size+10, cx+size-10, cy+size-10), fill=(180, 160, 140))
                else:
                    draw.rectangle((cx-size, cy-size, cx+size, cy+size), fill=color, outline=(0,0,0))
                    if hollow: draw.rectangle((cx-size+10, cy-size+10, cx+size-10, cy+size-10), fill=(180, 160, 140))
    draw.rectangle((0, q_row*CELL, CANVAS, (q_row+1)*CELL), outline=(255, 200, 50), width=5)
    img.save(path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated/quarto_v1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260521)
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    records = []
    rng = random.Random(args.seed)
    for i in range(args.count):
        board, q_row, shared = build_state(rng)
        img_name = f"images/{i:05d}.png"
        render(board, q_row, out_dir / img_name)
        ans = shared if shared else 'none'
        records.append({'id': f'r_quarto_v1-{i}', 'media': [img_name], 'messages': [{'role': 'user', 'question': '<image> This is a Quarto board. Do the four pieces in the yellow-outlined row share a common attribute (Tall/Short, Round/Square, Hollow/Solid, White/Black)? If so, name one shared attribute. Otherwise answer none.', 'answer': ans}]})
    
    with open(out_dir / 'vis_scaling_simple_mm.jsonl', 'w') as f:
        for r in records: f.write(json.dumps(r) + '\n')
    print(f'Wrote {args.count} Quarto records to {args.out_dir}')

if __name__ == "__main__":
    main()
