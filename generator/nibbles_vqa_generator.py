#!/usr/bin/env python3
"""Generate deterministic VQA samples for Nibbles / Snake."""

from __future__ import annotations

import argparse, json, random
from pathlib import Path
from typing import Dict, List, Sequence, Tuple
from PIL import Image, ImageDraw

VERSION = "nibbles_v1.0.0"
SCRIPT_NAME = "nibbles_vqa_generator.py"
CANVAS = 600
N = 10
CELL = CANVAS // N
RULE_SOURCE = "original/批次 5-0521.md:Nibbles; vendor/nibbles/wormy.py"
DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def next_head(head: Tuple[int, int], direction: str) -> Tuple[int, int]:
    dr, dc = DIRS[direction]
    return head[0] + dr, head[1] + dc


def collision(state: Dict) -> bool:
    nxt = next_head(tuple(state["snake"][0]), state["direction"])
    if not (0 <= nxt[0] < N and 0 <= nxt[1] < N):
        return True
    body = {tuple(x) for x in state["snake"][:-1]}
    return nxt in body


def apple_direction(state: Dict) -> str:
    hr, hc = state["snake"][0]
    ar, ac = state["apple"]
    vertical = "north" if ar < hr else "south" if ar > hr else "same row"
    horizontal = "west" if ac < hc else "east" if ac > hc else "same column"
    if vertical.startswith("same"):
        return horizontal
    if horizontal.startswith("same"):
        return vertical
    return f"{vertical}-{horizontal}"


def build_collision_state(rng: random.Random) -> Dict:
    if rng.choice([True, False]):
        snake = [[4, 4], [4, 3], [5, 3], [5, 4], [5, 5], [4, 5]]
        direction = "right"
    else:
        snake = [[0, rng.randint(3, 6)], [1, rng.randint(3, 6)], [2, rng.randint(3, 6)]]
        direction = "up"
        c = snake[0][1]
        snake = [[0, c], [1, c], [2, c], [3, c]]
    apple = [7, 7]
    return {"kind": "next_collision", "grid_size": [N, N], "snake": snake, "direction": direction, "apple": apple}


def build_apple_direction_state(rng: random.Random) -> Dict:
    head = [rng.randint(3, 6), rng.randint(3, 6)]
    direction = rng.choice(list(DIRS))
    snake = [head, [head[0], head[1] - 1], [head[0] + 1, head[1] - 1], [head[0] + 1, head[1]]]
    offsets = [(-3, -2), (-2, 3), (3, -2), (2, 3), (-3, 0), (0, 3)]
    dr, dc = rng.choice(offsets)
    apple = [max(0, min(N - 1, head[0] + dr)), max(0, min(N - 1, head[1] + dc))]
    return {"kind": "apple_direction", "grid_size": [N, N], "snake": snake, "direction": direction, "apple": apple}


def solve(state: Dict) -> str:
    if state["kind"] == "next_collision":
        return "yes" if collision(state) else "no"
    if state["kind"] == "apple_direction":
        return apple_direction(state)
    raise ValueError(state["kind"])


def cell_box(pos: Sequence[int], inset: int = 8) -> Tuple[int, int, int, int]:
    r, c = pos
    return c * CELL + inset, r * CELL + inset, (c + 1) * CELL - inset, (r + 1) * CELL - inset


def render(state: Dict, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), (21, 28, 32))
    draw = ImageDraw.Draw(img)
    for p in range(0, CANVAS + 1, CELL):
        draw.line((p, 0, p, CANVAS), fill=(43, 55, 61), width=1)
        draw.line((0, p, CANVAS, p), fill=(43, 55, 61), width=1)
    ax0, ay0, ax1, ay1 = cell_box(state["apple"], 10)
    draw.ellipse((ax0, ay0, ax1, ay1), fill=(225, 50, 65), outline=(255, 235, 235), width=3)
    snake = state["snake"]
    for i, pos in enumerate(reversed(snake)):
        is_head = pos == snake[0]
        fill = (63, 190, 106) if is_head else (46, 138, 82)
        box = cell_box(pos, 6)
        draw.rounded_rectangle(box, radius=8, fill=fill, outline=(220, 245, 226), width=4 if is_head else 2)
    hr, hc = snake[0]
    cx, cy = hc * CELL + CELL // 2, hr * CELL + CELL // 2
    dr, dc = DIRS[state["direction"]]
    end = (cx + dc * 22, cy + dr * 22)
    draw.line((cx, cy, end[0], end[1]), fill=(250, 250, 250), width=5)
    if state["direction"] == "up": pts = [(end[0], end[1] - 10), (end[0] - 8, end[1] + 4), (end[0] + 8, end[1] + 4)]
    elif state["direction"] == "down": pts = [(end[0], end[1] + 10), (end[0] - 8, end[1] - 4), (end[0] + 8, end[1] - 4)]
    elif state["direction"] == "left": pts = [(end[0] - 10, end[1]), (end[0] + 4, end[1] - 8), (end[0] + 4, end[1] + 8)]
    else: pts = [(end[0] + 10, end[1]), (end[0] - 4, end[1] - 8), (end[0] - 4, end[1] + 8)]
    draw.polygon(pts, fill=(250, 250, 250))
    img.save(path)


def record(idx: int, seed: int, state: Dict, answer: str, media: str) -> Dict:
    if state["kind"] == "next_collision":
        q = "<image> This is a Nibbles/Snake grid. The snake head has a white arrow showing its current direction. If the snake moves one grid square forward, will it collide with a wall or its own body? Answer only yes or no."
        choices, atype, diff, score, depth = ["yes", "no"], "yes_no", "medium", 0.55, 1
    else:
        q = "<image> This is a Nibbles/Snake grid. The red apple and the snake head are visible. Relative to the snake head, which direction is the apple? Answer with one of north, south, east, west, north-east, north-west, south-east, or south-west."
        choices, atype, diff, score, depth = ["north", "south", "east", "west", "north-east", "north-west", "south-east", "south-west"], "string", "easy", 0.35, 1
    return {"id": f"r_nibbles_v1-{seed}-{idx:05d}", "media": [media], "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}], "metadata": {"classification": {"domain": "games", "task": "nibbles_snake_state_prediction", "reasoning_type": "simulation", "visual_type": "grid_board", "rule_delivery_mode": "explicit_text_prompt"}, "dataset": {"slug": "nibbles_v1", "version": VERSION}, "provenance": {"source": "https://inventwithpython.com/blog/i-need-practice-programming-49-ideas-for-game-clones-to-code.html#nibbles", "method": "deterministic_rule_simulation", "seed": seed, "index": idx, "seed_description": "Snake body list, direction, and apple location on a 10x10 grid.", "generator": f"{SCRIPT_NAME}@{VERSION}", "rule_source": RULE_SOURCE}, "gt": {"answer": answer, "answer_text": answer, "answer_type": atype, "choices": choices, "validator": {"kind": "exact_match", "solution": answer}}, "instance": {"difficulty": diff, "complexity_score": score, "reasoning_depth": depth, "visual_load": len(state["snake"]) / (N * N), "tags": ["nibbles", "snake", "collision", "grid"], "raw_state": state}}}


def write_jsonl(items: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed); records = []
    builders = [build_collision_state, build_apple_direction_state]
    for idx in range(count):
        s = rng.randint(10_000_000, 999_999_999)
        state = builders[idx % 2](random.Random(s))
        ans = solve(state); img = f"images/{idx:05d}.png"; render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "nibbles_v1.rule", "rule": "The snake moves one grid cell forward; collision occurs at walls or occupied body cells."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": solve(r["metadata"]["instance"]["raw_state"]) == r["metadata"]["gt"]["answer"], "reason": "snake-state verifier", "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "nibbles_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "medium", "reasoning_max": "high", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "reproduce_command": f"python3 generator/{SCRIPT_NAME} --count {len(records)} --seed {seed} --out-dir {out_dir}", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(q["keep"] for q in quality): raise RuntimeError("quality verification failed")
    return records


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/nibbles_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Nibbles VQA records to {a.out_dir}")


if __name__ == "__main__": main()

