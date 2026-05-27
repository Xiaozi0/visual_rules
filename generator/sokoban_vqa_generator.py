#!/usr/bin/env python3
"""Generate deterministic VQA samples for Sokoban."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "sokoban_v1.0.0"
SCRIPT_NAME = "sokoban_vqa_generator.py"
CANVAS = 600
N = 8
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Sokoban"

# Colors
BG = (240, 240, 240)
WALL = (100, 100, 100)
GRID = (200, 200, 200)
TARGET = (220, 50, 50)
BOX = (180, 120, 50)
BOX_ON_TARGET = (50, 180, 50)
PLAYER = (50, 100, 220)
HIGHLIGHT = (255, 200, 50)

@dataclass
class SokobanState:
    kind: str
    walls: set[Tuple[int, int]]
    targets: set[Tuple[int, int]]
    boxes: set[Tuple[int, int]]
    player: Tuple[int, int]
    question_box: Tuple[int, int] | None
    question_dir: str | None

def build_state(rng: random.Random, kind: str) -> SokobanState:
    # Build a simple room
    walls = set()
    for r in range(N):
        for c in range(N):
            if r == 0 or r == N - 1 or c == 0 or c == N - 1:
                walls.add((r, c))
    
    # Add some random inner walls
    for _ in range(rng.randint(2, 6)):
        r, c = rng.randint(1, N - 2), rng.randint(1, N - 2)
        walls.add((r, c))

    empty = [(r, c) for r in range(1, N - 1) for c in range(1, N - 1) if (r, c) not in walls]
    rng.shuffle(empty)
    
    num_items = rng.randint(3, 5)
    targets = set(empty[:num_items])
    boxes = set(empty[num_items:num_items*2])
    player = empty[num_items*2]

    # Randomly put some boxes on targets
    if rng.choice([True, False]):
        boxes.pop()
        boxes.add(list(targets)[0])
    if rng.choice([True, False]) and num_items > 3:
        boxes.pop()
        boxes.add(list(targets)[1])

    question_box = None
    question_dir = None
    if kind == "push_legal":
        question_box = rng.choice(list(boxes))
        question_dir = rng.choice(["up", "down", "left", "right"])
        # Sometimes force it to be legal/illegal
        if rng.choice([True, False]):
            dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[question_dir]
            pr, pc = question_box[0] - dr, question_box[1] - dc
            if (pr, pc) not in walls and (pr, pc) not in boxes:
                player = (pr, pc)

    return SokobanState(kind, walls, targets, boxes, player, question_box, question_dir)

def is_push_legal(state: SokobanState) -> bool:
    if not state.question_box or not state.question_dir:
        return False
    dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[state.question_dir]
    
    # To push a box, player must be directly behind it
    pr, pc = state.question_box[0] - dr, state.question_box[1] - dc
    if state.player != (pr, pc):
        return False
        
    # The space behind the box must be empty or a target (no wall, no box)
    nr, nc = state.question_box[0] + dr, state.question_box[1] + dc
    if (nr, nc) in state.walls or (nr, nc) in state.boxes:
        return False
        
    return True

def count_on_target(state: SokobanState) -> int:
    return len(state.boxes.intersection(state.targets))

def solve(state: SokobanState) -> str:
    if state.kind == "count_on_target":
        return str(count_on_target(state))
    elif state.kind == "push_legal":
        return "yes" if is_push_legal(state) else "no"
    raise ValueError(state.kind)

def render(state: SokobanState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=GRID, width=1)
        draw.line((0, p, CANVAS, p), fill=GRID, width=1)
        
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL, r * CELL
            x1, y1 = (c + 1) * CELL, (r + 1) * CELL
            
            if (r, c) in state.walls:
                draw.rectangle((x0, y0, x1, y1), fill=WALL, outline=GRID)
            
            if (r, c) in state.targets:
                cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=TARGET)
                
            if (r, c) in state.boxes:
                color = BOX_ON_TARGET if (r, c) in state.targets else BOX
                outline = HIGHLIGHT if (r, c) == state.question_box else (0, 0, 0)
                width = 5 if (r, c) == state.question_box else 2
                draw.rectangle((x0 + 10, y0 + 10, x1 - 10, y1 - 10), fill=color, outline=outline, width=width)
                
                # Draw lines for box texture
                draw.line((x0 + 10, y0 + 10, x1 - 10, y1 - 10), fill=(0, 0, 0), width=width)
                draw.line((x1 - 10, y0 + 10, x0 + 10, y1 - 10), fill=(0, 0, 0), width=width)

                if (r, c) == state.question_box and state.question_dir:
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[state.question_dir]
                    end_x = cx + dc * 30
                    end_y = cy + dr * 30
                    draw.line((cx, cy, end_x, end_y), fill=HIGHLIGHT, width=6)
                    # Simple arrow head
                    draw.ellipse((end_x - 5, end_y - 5, end_x + 5, end_y + 5), fill=HIGHLIGHT)
                
            if (r, c) == state.player:
                draw.ellipse((x0 + 15, y0 + 15, x1 - 15, y1 - 15), fill=PLAYER, outline=(0, 0, 0), width=2)
                
    img.save(path)

def record(idx: int, seed: int, state: SokobanState, answer: str, media: str) -> Dict:
    if state.kind == "count_on_target":
        q = "<image> This is a Sokoban board. Gray squares are walls, small red circles are targets, brown/green squares are boxes, and the blue circle is the player. How many boxes are currently on targets? Answer with a number only."
        choices, atype, diff, score = ["0", "1", "2", "3", "4", "5"], "count", "easy", 0.3
    else:
        q = f"<image> This is a Sokoban board. The yellow-outlined box has an arrow pointing {state.question_dir}. Can the player legally push this box one step in the direction of the arrow? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "medium", 0.6
        
    return {
        "id": f"r_sokoban_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "sokoban_mechanics",
                "reasoning_type": "simulation",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "sokoban_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Sokoban",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "8x8 Sokoban board with randomly placed walls, targets, boxes, and player.",
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
                "tags": ["sokoban", "push", "grid"],
                "raw_state": {
                    "kind": state.kind,
                    "walls": list(state.walls),
                    "targets": list(state.targets),
                    "boxes": list(state.boxes),
                    "player": state.player,
                    "question_box": state.question_box,
                    "question_dir": state.question_dir
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
        kind = ["count_on_target", "push_legal"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
        
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([
        {"id": "sokoban_v1.push", "rule": "A player can push a box if the player is directly behind it and the square in front of the box is empty or a target."}
    ], out_dir / "rules.jsonl")
    
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    
    manifest = {
        "dataset": "sokoban_v1",
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
    p.add_argument("--out-dir", default="generated/sokoban_v1")
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--seed", type=int, default=20260521)
    a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Sokoban VQA records to {a.out_dir}")

if __name__ == "__main__":
    main()
