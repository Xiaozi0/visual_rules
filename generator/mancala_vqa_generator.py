#!/usr/bin/env python3
"""Generate deterministic VQA samples for Mancala."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "mancala_v1.0.0"
SCRIPT_NAME = "mancala_vqa_generator.py"
CANVAS = 600
RULE_SOURCE = "original/批次 5-0521.md:Mancala"

BG = (245, 240, 230)
BOARD = (140, 100, 60)
PIT = (80, 50, 20)
SEED = (220, 210, 200)
TEXT = (255, 255, 255)
HIGHLIGHT = (255, 200, 50)

@dataclass
class MancalaState:
    kind: str
    pits: List[int] # 0-5 player 1, 6 store 1, 7-12 player 2, 13 store 2
    question_pit: int
    extra_turn: bool
    num_seeds: int

def sowing(pits: List[int], start_pit: int) -> Tuple[List[int], bool]:
    temp = pits[:]
    seeds = temp[start_pit]
    temp[start_pit] = 0
    curr = start_pit
    
    while seeds > 0:
        curr = (curr + 1) % 14
        # Simplified rules: drop seeds everywhere
        temp[curr] += 1
        seeds -= 1
        
    extra_turn = (curr == 6) # Ended in P1 store
    return temp, extra_turn

def build_state(rng: random.Random, kind: str) -> MancalaState:
    # 0-5: P1 pits, 6: P1 store, 7-12: P2 pits, 13: P2 store
    pits = [4] * 14
    pits[6] = 0
    pits[13] = 0
    
    # Randomly distribute seeds
    for _ in range(rng.randint(5, 15)):
        p1 = rng.randint(0, 5)
        p2 = rng.randint(7, 12)
        pits[p1] = max(0, pits[p1] + rng.randint(-2, 2))
        pits[p2] = max(0, pits[p2] + rng.randint(-2, 2))
        pits[6] += rng.randint(0, 3)
        pits[13] += rng.randint(0, 3)

    q_pit = rng.randint(0, 5)
    _, extra_turn = sowing(pits, q_pit)
    num_seeds = pits[q_pit]
    
    if kind == "extra_turn":
        # Force a pit that gives extra turn if possible
        candidates = [i for i in range(6) if (i + pits[i]) % 14 == 6]
        if candidates and rng.choice([True, False]):
            q_pit = rng.choice(candidates)
            extra_turn = True
        else:
            extra_turn = (q_pit + pits[q_pit]) % 14 == 6
            
    return MancalaState(kind, pits, q_pit, extra_turn, num_seeds)

def solve(state: MancalaState) -> str:
    if state.kind == "count_seeds":
        return str(state.num_seeds)
    elif state.kind == "extra_turn":
        return "yes" if state.extra_turn else "no"
    raise ValueError(state.kind)

def render(state: MancalaState, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Board
    draw.rounded_rectangle((50, 150, 550, 450), radius=30, fill=BOARD)
    
    # Stores
    draw.rounded_rectangle((70, 170, 120, 430), radius=20, fill=PIT) # P2 store
    draw.rounded_rectangle((480, 170, 530, 430), radius=20, fill=PIT) # P1 store
    
    # Pits
    for i in range(6):
        # Bottom row (P1: 0-5)
        x = 150 + i * 55
        y = 330
        draw.ellipse((x, y, x + 45, y + 45), fill=PIT)
        if state.question_pit == i:
            draw.ellipse((x - 5, y - 5, x + 50, y + 50), outline=HIGHLIGHT, width=4)
            
        # Top row (P2: 12-7)
        x = 150 + i * 55
        y = 225
        draw.ellipse((x, y, x + 45, y + 45), fill=PIT)
        
    # Draw seeds (dots)
    # Bottom row
    for i in range(6):
        num = state.pits[i]
        x_base = 150 + i * 55 + 22
        y_base = 330 + 22
        for s in range(min(num, 8)):
            angle = s * 45
            import math
            sx = x_base + 12 * math.cos(math.radians(angle))
            sy = y_base + 12 * math.sin(math.radians(angle))
            draw.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=SEED)
            
    # Top row (P2 pits 12 to 7)
    for i in range(6):
        num = state.pits[12 - i]
        x_base = 150 + i * 55 + 22
        y_base = 225 + 22
        for s in range(min(num, 8)):
            angle = s * 45
            import math
            sx = x_base + 12 * math.cos(math.radians(angle))
            sy = y_base + 12 * math.sin(math.radians(angle))
            draw.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=SEED)

    img.save(path)

def record(idx: int, seed: int, state: MancalaState, answer: str, media: str) -> Dict:
    if state.kind == "count_seeds":
        q = "<image> This is a Mancala board. The yellow-outlined pit is on the bottom row. How many seeds are in this pit? Answer with a number only."
        atype, diff, score = "count", "easy", 0.3
    else:
        q = "<image> This is a Mancala board. If the player sows the seeds from the yellow-outlined pit (counter-clockwise), will they get an extra turn? (An extra turn is awarded if the last seed drops into the player's large store on the right). Answer only yes or no."
        atype, diff, score = "yes_no", "medium", 0.6
        
    return {
        "id": f"r_mancala_v1-{seed}-{idx:05d}",
        "media": [media],
        "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": [], "hint": ""}],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "mancala_logic",
                "reasoning_type": "numerical",
                "visual_type": "grid_board",
                "rule_delivery_mode": "explicit_text_prompt"
            },
            "dataset": {"slug": "mancala_v1", "version": VERSION},
            "provenance": {
                "source": "Invent with Python Mancala",
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
                "visual_load": 0.6,
                "tags": ["mancala", "counting", "game-rules"],
                "raw_state": {
                    "pits": state.pits,
                    "question_pit": state.question_pit,
                    "extra_turn": state.extra_turn,
                    "num_seeds": state.num_seeds
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
        kind = ["count_seeds", "extra_turn"][idx % 2]
        state = build_state(random.Random(s), kind)
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "mancala_v1.extra_turn", "rule": "A player gets an extra turn if the last seed drops into their store."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": True, "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "mancala_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "medium", "reasoning_max": "medium", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/mancala_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Mancala VQA records to {a.out_dir}")

if __name__ == "__main__": main()
