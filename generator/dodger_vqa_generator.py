#!/usr/bin/env python3
"""Generate deterministic VQA samples for the Dodger game clone.

The script renders square, text-free Dodger states and emits JSONL records in
the project VQA format. It uses a simplified deterministic abstraction of the
original Pygame rules: rectangular player/enemy sprites, downward enemy motion,
and axis-aligned rectangle collision.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw


VERSION = "dodger_vqa_v1.0.0"
SCRIPT_NAME = "dodger_vqa_generator.py"
CANVAS = 600
GRID_CELLS = 10
CELL = CANVAS // GRID_CELLS
SPRITE_SIZE = 44
PLAYER_SIZE = SPRITE_SIZE
MOVE_STEP = CELL
RULE_SOURCE = "original/批次 5-0521.md:Dodger; vendor/dodger/dodger.py"
COLORS = {
    "red": (226, 55, 68),
    "orange": (242, 142, 43),
    "purple": (138, 90, 180),
    "cyan": (37, 171, 194),
    "green": (69, 178, 107),
    "yellow": (235, 196, 64),
}
PLAYER_COLOR = (58, 121, 216)
BG = (18, 20, 24)
GRID = (42, 46, 52)
WHITE = (238, 240, 244)


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def moved(self, dx: int = 0, dy: int = 0) -> "Rect":
        return Rect(self.x + dx, self.y + dy, self.w, self.h)

    def clamp_to_canvas(self) -> "Rect":
        return Rect(
            max(0, min(CANVAS - self.w, self.x)),
            max(0, min(CANVAS - self.h, self.y)),
            self.w,
            self.h,
        )

    def intersects(self, other: "Rect") -> bool:
        return (
            self.left < other.right
            and self.right > other.left
            and self.top < other.bottom
            and self.bottom > other.top
        )


@dataclass(frozen=True)
class Enemy:
    color_name: str
    rect: Rect
    speed: int

    def after_steps(self, steps: int) -> Rect:
        return self.rect.moved(dy=self.speed * steps)


@dataclass(frozen=True)
class DodgerState:
    player: Rect
    enemies: List[Enemy]


def rect_distance(a: Rect, b: Rect) -> float:
    ax = max(a.left - b.right, b.left - a.right, 0)
    ay = max(a.top - b.bottom, b.top - a.bottom, 0)
    return math.hypot(ax, ay)


def cell_rect(col: int, row: int, size: int = SPRITE_SIZE) -> Rect:
    inset = (CELL - size) // 2
    return Rect(col * CELL + inset, row * CELL + inset, size, size)


def move_player(player: Rect, move: str) -> Rect:
    deltas = {
        "Left": (-MOVE_STEP, 0),
        "Right": (MOVE_STEP, 0),
        "Up": (0, -MOVE_STEP),
        "Down": (0, MOVE_STEP),
        "Stay": (0, 0),
    }
    dx, dy = deltas[move]
    return player.moved(dx, dy).clamp_to_canvas()


def collides(player: Rect, enemies: Iterable[Enemy], steps: int = 1) -> bool:
    return any(player.intersects(enemy.after_steps(steps)) for enemy in enemies)


def time_to_collision(player: Rect, enemy: Enemy, max_steps: int = 80) -> int | None:
    for step in range(1, max_steps + 1):
        if player.intersects(enemy.after_steps(step)):
            return step
    return None


def draw_arrow(draw: ImageDraw.ImageDraw, x: int, y0: int, y1: int, color: Tuple[int, int, int]) -> None:
    draw.line((x, y0, x, y1), fill=color, width=4)
    draw.polygon([(x, y1 + 10), (x - 8, y1 - 4), (x + 8, y1 - 4)], fill=color)


def render_state(state: DodgerState, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)

    for pos in range(0, CANVAS + 1, CELL):
        draw.line((pos, 0, pos, CANVAS), fill=GRID, width=1)
        draw.line((0, pos, CANVAS, pos), fill=GRID, width=1)

    for enemy in state.enemies:
        color = COLORS[enemy.color_name]
        r = enemy.rect
        future = enemy.after_steps(1)
        draw.rectangle((future.left, future.top, future.right, future.bottom), outline=color, width=3)
        x = int(r.center[0])
        y0 = r.bottom + 4
        y1 = max(y0 + 8, future.top - 6)
        draw_arrow(draw, x, y0, y1, color)

    p = state.player
    draw.rounded_rectangle((p.left, p.top, p.right, p.bottom), radius=4, fill=PLAYER_COLOR, outline=WHITE, width=3)
    visor = (p.left + 10, p.top + 9, p.right - 10, p.top + 20)
    draw.rounded_rectangle(visor, radius=4, fill=(177, 215, 255), outline=(16, 66, 130), width=2)

    for enemy in state.enemies:
        color = COLORS[enemy.color_name]
        r = enemy.rect
        draw.rectangle((r.left, r.top, r.right, r.bottom), fill=color, outline=WHITE, width=2)
        draw.line((r.left + 6, r.top + 6, r.right - 6, r.bottom - 6), fill=(35, 35, 38), width=3)
        draw.line((r.left + 6, r.bottom - 6, r.right - 6, r.top + 6), fill=(35, 35, 38), width=3)

    image.save(path)


def build_first_collision_state(rng: random.Random) -> DodgerState:
    player_col = rng.choice([4, 5])
    player = cell_rect(player_col, 8)
    enemies = [
        Enemy("red", cell_rect(player_col, 5), CELL),
        Enemy("orange", cell_rect(player_col - 2, 6), CELL),
        Enemy("purple", cell_rect(player_col + 2, 4), CELL * 2),
        Enemy("cyan", cell_rect(player_col, 2), CELL),
    ]
    return DodgerState(player, enemies)


def build_safe_move_state(rng: random.Random) -> DodgerState:
    player_col = rng.choice([4, 5])
    player = cell_rect(player_col, 7)
    enemies = [
        Enemy("red", cell_rect(player_col - 1, 6), CELL),
        Enemy("orange", cell_rect(player_col + 1, 6), CELL),
        Enemy("purple", cell_rect(player_col, 4), CELL * 3),
        Enemy("cyan", cell_rect(player_col, 5), CELL * 3),
    ]
    return DodgerState(player, enemies)


def first_collision_answer(state: DodgerState) -> str:
    hits = []
    for enemy in state.enemies:
        step = time_to_collision(state.player, enemy)
        if step is not None:
            hits.append((step, enemy.color_name))
    if not hits:
        raise ValueError("first-collision state has no colliding enemy")
    hits.sort()
    return hits[0][1]


def safe_move_answer(state: DodgerState) -> str:
    candidates = ["Left", "Right", "Up", "Down"]
    safe = []
    for move in candidates:
        moved = move_player(state.player, move)
        if not collides(moved, state.enemies, steps=1):
            min_gap = min(rect_distance(moved, enemy.after_steps(1)) for enemy in state.enemies)
            safe.append((min_gap, move))
    if not safe:
        raise ValueError("safe-move state has no safe answer")
    safe.sort(reverse=True)
    return safe[0][1]


def record(
    *,
    idx: int,
    seed: int,
    state: DodgerState,
    question_kind: str,
    answer_text: str,
    media_path: str,
) -> Dict:
    if question_kind == "first_collision":
        question = (
            "<image> In this grid version of Dodger, each enemy falls straight down to the "
            "outlined square shown by its colored arrow each time step, and the blue player "
            "stays still. Which colored enemy will collide with the player first? Answer with "
            "the color name only."
        )
        choices = [enemy.color_name for enemy in state.enemies]
        answer_type = "string"
        difficulty = "medium"
        complexity = 0.55
    elif question_kind == "safe_move":
        question = (
            "<image> In this grid version of Dodger, each enemy falls straight down to the "
            "outlined square shown by its colored arrow in the next time step. The blue player "
            "may move exactly one grid square Left, Right, Up, or Down before the enemies fall. "
            "Which move gives the largest collision-free gap after that next time step? Answer "
            "with one direction only."
        )
        choices = ["Left", "Right", "Up", "Down"]
        answer_type = "multiple_choice"
        difficulty = "medium"
        complexity = 0.6
    else:
        raise ValueError(question_kind)

    return {
        "id": f"r_dodger_vqa_v1-{seed}-{idx:05d}",
        "media": [media_path],
        "messages": [
            {
                "role": "user",
                "question": question,
                "answer": answer_text,
                "options": {},
                "choices": choices,
                "hint": "",
            }
        ],
        "metadata": {
            "classification": {
                "domain": "games",
                "task": "dodger_collision_avoidance",
                "reasoning_type": "simulation",
                "visual_type": "scene_objects",
                "rule_delivery_mode": "explicit_text_prompt",
            },
            "dataset": {
                "slug": "dodger_vqa_v1",
                "source_id": "invent_with_python_dodger",
                "family": "action_game_static_state_simulation",
                "upstream_name": "Invent with Python Dodger",
                "title": "Dodger Collision and Avoidance VQA",
                "version": VERSION,
            },
            "provenance": {
                "source": "https://inventwithpython.com/blog/i-need-practice-programming-49-ideas-for-game-clones-to-code.html#dodger",
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "seed_description": "Dodger player rectangle, enemy rectangles, and one-step downward velocity arrows.",
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE,
            },
            "gt": {
                "answer": answer_text,
                "answer_text": answer_text,
                "answer_type": answer_type,
                "choices": choices,
                "validator": {
                    "kind": "exact_match",
                    "solution": answer_text,
                },
            },
            "instance": {
                "difficulty": difficulty,
                "complexity_score": complexity,
                "tags": ["dodger", "collision", "falling-enemies", "static-frame-simulation"],
                "question_kind": question_kind,
                "raw_state": {
                    "canvas": [CANVAS, CANVAS],
                    "grid_cells": [GRID_CELLS, GRID_CELLS],
                    "player_move_step": MOVE_STEP,
                    "player": asdict(state.player),
                    "enemies": [
                        {
                            "color": enemy.color_name,
                            "rect": asdict(enemy.rect),
                            "speed": enemy.speed,
                            "time_to_collision_if_stay": time_to_collision(state.player, enemy),
                        }
                        for enemy in state.enemies
                    ],
                },
            },
        },
    }


def write_jsonl(records: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_rules(path: Path) -> None:
    rules = [
        {
            "id": "dodger_vqa_v1.playfield",
            "task": "dodger_collision_avoidance",
            "rule": f"The game is represented on a {GRID_CELLS} x {GRID_CELLS} grid inside a 600 x 600 square playfield.",
        },
        {
            "id": "dodger_vqa_v1.motion",
            "task": "dodger_collision_avoidance",
            "rule": "Enemies fall straight downward; the colored arrow points from each enemy's current square to its next square.",
        },
        {
            "id": "dodger_vqa_v1.collision",
            "task": "dodger_collision_avoidance",
            "rule": "The player is hit when its axis-aligned rectangle intersects any enemy rectangle after motion.",
        },
        {
            "id": "dodger_vqa_v1.player_move",
            "task": "dodger_collision_avoidance",
            "rule": "For safe-move questions, the player moves exactly one grid square in the chosen cardinal direction before collision is evaluated.",
        },
    ]
    write_jsonl(rules, path)


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    if count < 1:
        raise ValueError("count must be positive")
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []

    builders = [
        ("first_collision", build_first_collision_state, first_collision_answer),
        ("safe_move", build_safe_move_state, safe_move_answer),
    ]
    for idx in range(count):
        sample_seed = rng.randint(10_000_000, 999_999_999)
        sample_rng = random.Random(sample_seed)
        question_kind, builder, solver = builders[idx % len(builders)]
        state = builder(sample_rng)
        answer = solver(state)
        image_name = f"{idx:05d}.png"
        render_state(state, image_dir / image_name)
        records.append(
            record(
                idx=idx,
                seed=sample_seed,
                state=state,
                question_kind=question_kind,
                answer_text=answer,
                media_path=f"images/{image_name}",
            )
        )

    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_rules(out_dir / "rules.jsonl")
    quality = [
        {
            "id": item["id"],
            "keep": True,
            "reason": "deterministic rectangle simulation verified",
            "answer": item["metadata"]["gt"]["answer"],
        }
        for item in records
    ]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "dataset": "dodger_vqa_v1",
        "version": VERSION,
        "generator": SCRIPT_NAME,
        "count": len(records),
        "seed": seed,
        "rule_source": RULE_SOURCE,
        "format": "format_docs/VQA_DATA_FORMAT.md",
        "classification": "format_docs/classification.md",
        "outputs": {
            "records": "vis_scaling_simple_mm.jsonl",
            "rules": "rules.jsonl",
            "quality_report": "quality_report.json",
            "images": "images/",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated/dodger_vqa_v1")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260521)
    args = parser.parse_args()
    records = generate(Path(args.out_dir), args.count, args.seed)
    print(f"Wrote {len(records)} Dodger VQA records to {args.out_dir}")


if __name__ == "__main__":
    main()
