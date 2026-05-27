#!/usr/bin/env python3
"""Playable Bloxorz / flip-block game engine and renderer.

The puzzle uses a 2x1 block that can stand upright on one tile or lie across
two adjacent tiles. A move rolls the block one step in one of four directions.
Any state that touches a missing tile or leaves the board is illegal.

This module provides:
- a terminal game (`play`)
- a square PNG renderer (`render`)
- deterministic puzzle sampling for VQA generation
"""

from __future__ import annotations

import argparse
import json
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw


VERSION = "flip_blocks_game_v1.0.0"
GENERATOR_TAG = "codex"
CANVAS = 640
BG = (241, 245, 248)
PANEL = (255, 255, 255)
GRID = (201, 211, 221)
TILE = (233, 240, 247)
TILE_ALT = (225, 233, 242)
VOID = (190, 199, 209)
BLOCK = (63, 155, 228)
BLOCK_EDGE = (25, 92, 148)
GOAL = (224, 70, 64)
GOAL_EDGE = (135, 34, 32)
INK = (31, 38, 47)
SPONGE = (225, 211, 74)
SPONGE_DARK = (187, 174, 51)
PANTS = (176, 105, 45)
PANTS_DARK = (133, 75, 28)
SHIRT = (244, 244, 232)
TIE = (203, 45, 52)

MOVES = ("up", "down", "left", "right")
MOVE_ALIASES = {
    "w": "up",
    "up": "up",
    "n": "up",
    "north": "up",
    "s": "down",
    "down": "down",
    "south": "down",
    "a": "left",
    "left": "left",
    "l": "left",
    "west": "left",
    "d": "right",
    "right": "right",
    "r": "right",
    "e": "right",
    "east": "right",
}


@dataclass(frozen=True)
class Pose:
    cells: tuple[tuple[int, int], ...]

    @property
    def standing(self) -> bool:
        return len(self.cells) == 1


@dataclass(frozen=True)
class Puzzle:
    rows: int
    cols: int
    board: tuple[str, ...]
    start: Pose
    goal: tuple[int, int]
    min_steps: int | None


def pose(cells: Sequence[tuple[int, int]]) -> Pose:
    return Pose(tuple(sorted(cells)))


def in_bounds(rows: int, cols: int, cell: tuple[int, int]) -> bool:
    r, c = cell
    return 0 <= r < rows and 0 <= c < cols


def valid(board: tuple[str, ...], p: Pose) -> bool:
    rows, cols = len(board), len(board[0])
    return all(in_bounds(rows, cols, cell) and board[cell[0]][cell[1]] == "." for cell in p.cells)


def move_pose(p: Pose, move: str) -> Pose:
    cells = list(p.cells)
    if len(cells) == 1:
        r, c = cells[0]
        if move == "up":
            return pose([(r - 2, c), (r - 1, c)])
        if move == "down":
            return pose([(r + 1, c), (r + 2, c)])
        if move == "left":
            return pose([(r, c - 2), (r, c - 1)])
        if move == "right":
            return pose([(r, c + 1), (r, c + 2)])
    else:
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            row = r1
            left = min(c1, c2)
            right = max(c1, c2)
            if move == "left":
                return pose([(row, left - 1)])
            if move == "right":
                return pose([(row, right + 1)])
            if move == "up":
                return pose([(row - 1, left), (row - 1, right)])
            if move == "down":
                return pose([(row + 1, left), (row + 1, right)])
        else:
            col = c1
            top = min(r1, r2)
            bottom = max(r1, r2)
            if move == "up":
                return pose([(top - 1, col)])
            if move == "down":
                return pose([(bottom + 1, col)])
            if move == "left":
                return pose([(top, col - 1), (bottom, col - 1)])
            if move == "right":
                return pose([(top, col + 1), (bottom, col + 1)])
    raise ValueError(move)


def shortest_path(board: tuple[str, ...], start: Pose, goal: tuple[int, int]) -> int | None:
    queue: deque[tuple[Pose, int]] = deque([(start, 0)])
    seen = {start}
    while queue:
        state, dist = queue.popleft()
        if state.standing and state.cells[0] == goal:
            return dist
        for move in MOVES:
            nxt = move_pose(state, move)
            if nxt in seen or not valid(board, nxt):
                continue
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None


def neighbors(cell: tuple[int, int], rows: int, cols: int) -> list[tuple[int, int]]:
    r, c = cell
    out = []
    for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if 0 <= rr < rows and 0 <= cc < cols:
            out.append((rr, cc))
    return out


def random_connected_cells(rng: random.Random, rows: int, cols: int, size: int) -> set[tuple[int, int]]:
    start = (rng.randrange(rows), rng.randrange(cols))
    cells = {start}
    frontier = [start]
    while len(cells) < size:
        base = rng.choice(frontier)
        candidates = [nb for nb in neighbors(base, rows, cols) if nb not in cells]
        if not candidates:
            frontier = [cell for cell in frontier if any(nb not in cells for nb in neighbors(cell, rows, cols))]
            if not frontier:
                break
            continue
        nxt = rng.choice(candidates)
        cells.add(nxt)
        frontier.append(nxt)
    return cells


def connected(cells: set[tuple[int, int]], rows: int, cols: int) -> bool:
    start = next(iter(cells))
    queue = deque([start])
    seen = {start}
    while queue:
        cell = queue.popleft()
        for nb in neighbors(cell, rows, cols):
            if nb in cells and nb not in seen:
                seen.add(nb)
                queue.append(nb)
    return len(seen) == len(cells)


def board_from_cells(rows: int, cols: int, valid_cells: set[tuple[int, int]]) -> tuple[str, ...]:
    return tuple("".join("." if (r, c) in valid_cells else "#" for c in range(cols)) for r in range(rows))


def sample_puzzle(rng: random.Random, want_reachable: bool) -> Puzzle:
    for _ in range(1000):
        rows = rng.randint(5, 7)
        cols = rng.randint(5, 7)
        size = rng.randint(max(10, rows + cols), rows * cols - 1)
        cells = random_connected_cells(rng, rows, cols, size)
        if len(cells) < size or not connected(cells, rows, cols):
            continue
        board = board_from_cells(rows, cols, cells)
        start_cell = rng.choice(sorted(cells))
        goal_cell = rng.choice([cell for cell in sorted(cells) if cell != start_cell])
        start = pose([start_cell])
        dist = shortest_path(board, start, goal_cell)
        if (dist is not None) != want_reachable:
            continue
        return Puzzle(rows=rows, cols=cols, board=board, start=start, goal=goal_cell, min_steps=dist)
    raise RuntimeError("failed to sample a puzzle")


def stable_seed(seed: int, index: int) -> int:
    return seed * 1_000_003 + index * 97 + 17


def draw_round_rect(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], fill, outline, width: int = 1, radius: int = 8) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def iso_point(origin_x: float, origin_y: float, row: float, col: float, tile_w: float, tile_h: float) -> tuple[float, float]:
    return (origin_x + (col - row) * tile_w / 2, origin_y + (col + row) * tile_h / 2)


def tile_poly(origin_x: float, origin_y: float, row: float, col: float, tile_w: float, tile_h: float) -> list[tuple[float, float]]:
    cx, cy = iso_point(origin_x, origin_y, row, col, tile_w, tile_h)
    return [(cx, cy - tile_h / 2), (cx + tile_w / 2, cy), (cx, cy + tile_h / 2), (cx - tile_w / 2, cy)]


def shade(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(max(0, min(255, channel + delta)) for channel in color)


def draw_prism(
    draw: ImageDraw.ImageDraw,
    top: list[tuple[float, float]],
    height: float,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> None:
    lowered = [(x, y + height) for x, y in top]
    left = [top[3], top[2], lowered[2], lowered[3]]
    right = [top[1], top[2], lowered[2], lowered[1]]
    draw.polygon(left, fill=shade(fill, -38), outline=outline)
    draw.polygon(right, fill=shade(fill, -24), outline=outline)
    draw.polygon(top, fill=fill, outline=outline)


def draw_spongebob_marks(draw: ImageDraw.ImageDraw, front: list[tuple[float, float]]) -> None:
    xs = [p[0] for p in front]
    ys = [p[1] for p in front]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    cx = (x0 + x1) / 2
    width = x1 - x0
    height = y1 - y0

    eye_y = y0 + height * 0.28
    for ex in (cx - width * 0.14, cx + width * 0.14):
        draw.ellipse((ex - 9, eye_y - 7, ex + 9, eye_y + 8), fill=(255, 255, 255), outline=INK, width=1)
        draw.ellipse((ex - 4, eye_y - 2, ex + 4, eye_y + 5), fill=(64, 142, 198))
    draw.arc((cx - 28, y0 + height * 0.38, cx + 28, y0 + height * 0.62), start=15, end=165, fill=PANTS_DARK, width=2)
    draw.rectangle((cx - 9, y0 + height * 0.55, cx - 1, y0 + height * 0.66), fill=(255, 255, 255), outline=INK)
    draw.rectangle((cx + 1, y0 + height * 0.55, cx + 9, y0 + height * 0.66), fill=(255, 255, 255), outline=INK)
    for sx, sy, rr in ((x0 + width * 0.24, y0 + height * 0.72, 7), (x1 - width * 0.18, y0 + height * 0.42, 9), (x0 + width * 0.18, y0 + height * 0.20, 5)):
        draw.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=SPONGE_DARK)


def draw_spongebob_block(
    draw: ImageDraw.ImageDraw,
    top: list[tuple[float, float]],
    height: float,
    *,
    standing: bool,
) -> None:
    lowered = [(x, y + height) for x, y in top]
    front = [top[3], top[2], lowered[2], lowered[3]]
    side = [top[1], top[2], lowered[2], lowered[1]]

    draw.polygon(front, fill=SPONGE, outline=INK)
    draw.polygon(side, fill=shade(SPONGE, -18), outline=INK)
    draw.polygon(top, fill=shade(SPONGE, 8), outline=INK)

    if standing:
        xs = [p[0] for p in front]
        ys = [p[1] for p in front]
        y0, y1 = min(ys), max(ys)
        x0, x1 = min(xs), max(xs)
        shirt_y = y0 + (y1 - y0) * 0.70
        pants_y = y0 + (y1 - y0) * 0.80
        draw.polygon([(x0, shirt_y), (x1, shirt_y), (x1, pants_y), (x0, pants_y)], fill=SHIRT, outline=INK)
        draw.polygon([(x0, pants_y), (x1, pants_y), (x1, y1), (x0, y1)], fill=PANTS, outline=INK)
        cx = (x0 + x1) / 2
        draw.polygon([(cx, shirt_y + 4), (cx + 8, pants_y + 10), (cx, pants_y + 22), (cx - 8, pants_y + 10)], fill=TIE, outline=INK)
        draw_spongebob_marks(draw, front)
    else:
        cx = sum(x for x, _ in top) / 4
        cy = sum(y for _, y in top) / 4
        draw.ellipse((cx - 16, cy - 10, cx - 4, cy + 2), fill=(255, 255, 255), outline=INK)
        draw.ellipse((cx + 4, cy - 10, cx + 16, cy + 2), fill=(255, 255, 255), outline=INK)


def render_puzzle(puzzle: Puzzle, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), (174, 174, 174))
    draw = ImageDraw.Draw(img)

    tile_w = min(76.0, (CANVAS - 110) / max(puzzle.rows, puzzle.cols) * 1.55)
    tile_h = tile_w * 0.46
    origin_x = CANVAS / 2 + (puzzle.rows - puzzle.cols) * tile_w * 0.25
    origin_y = 125
    platform_depth = tile_h * 0.30

    all_points = []
    for r in range(puzzle.rows):
        for c in range(puzzle.cols):
            all_points.extend(tile_poly(origin_x, origin_y, r, c, tile_w, tile_h))
    min_x = min(x for x, _ in all_points)
    max_x = max(x for x, _ in all_points)
    min_y = min(y for _, y in all_points)
    max_y = max(y for _, y in all_points) + 120
    dx = (CANVAS - (max_x - min_x)) / 2 - min_x
    dy = (CANVAS - (max_y - min_y)) / 2 - min_y
    origin_x += dx
    origin_y += dy

    for r in range(puzzle.rows):
        for c in range(puzzle.cols):
            if puzzle.board[r][c] == "#":
                continue
            poly = tile_poly(origin_x, origin_y, r, c, tile_w, tile_h)
            fill = (235, 235, 231) if (r + c) % 2 == 0 else (47, 49, 50)
            draw_prism(draw, poly, platform_depth, fill, (93, 93, 90))

    gr, gc = puzzle.goal
    goal_poly = tile_poly(origin_x, origin_y, gr, gc, tile_w, tile_h)
    gcx = sum(x for x, _ in goal_poly) / 4
    gcy = sum(y for _, y in goal_poly) / 4
    diamond = [(gcx, gcy - tile_h * 0.44), (gcx + tile_w * 0.18, gcy), (gcx, gcy + tile_h * 0.44), (gcx - tile_w * 0.18, gcy)]
    draw.polygon(diamond, fill=GOAL, outline=GOAL_EDGE)

    if puzzle.start.standing:
        r, c = puzzle.start.cells[0]
        top = tile_poly(origin_x, origin_y, r, c, tile_w, tile_h)
        draw_spongebob_block(draw, top, tile_h * 1.75, standing=True)
    else:
        (r1, c1), (r2, c2) = puzzle.start.cells
        if r1 == r2:
            row = r1
            left = min(c1, c2)
            top1 = tile_poly(origin_x, origin_y, row, left, tile_w, tile_h)
            top2 = tile_poly(origin_x, origin_y, row, left + 1, tile_w, tile_h)
        else:
            top_row = min(r1, r2)
            col = c1
            top1 = tile_poly(origin_x, origin_y, top_row, col, tile_w, tile_h)
            top2 = tile_poly(origin_x, origin_y, top_row + 1, col, tile_w, tile_h)
        merged = [top1[0], top2[1], top2[2], top1[3]]
        draw_spongebob_block(draw, merged, tile_h * 0.95, standing=False)

    img.save(path)


def ascii_board(puzzle: Puzzle, state: Pose) -> str:
    rows = []
    occupied = set(state.cells)
    for r in range(puzzle.rows):
        row = []
        for c in range(puzzle.cols):
            if (r, c) == puzzle.goal:
                ch = "G"
            elif (r, c) in occupied:
                ch = "B"
            elif puzzle.board[r][c] == "#":
                ch = "#"
            else:
                ch = "."
            row.append(ch)
        rows.append(" ".join(row))
    return "\n".join(rows)


def play(puzzle: Puzzle) -> None:
    state = puzzle.start
    history: list[Pose] = []
    moves: list[str] = []

    print("Flip Blocks / Bloxorz")
    print("Controls: W/A/S/D or arrow names. q to quit, u to undo, r to reset.\n")
    print(f"Goal: stand upright on the red hole at {puzzle.goal}.")
    if puzzle.min_steps is not None:
        print(f"Shortest solution length: {puzzle.min_steps}\n")
    else:
        print("This puzzle instance is intentionally unreachable.\n")

    while True:
        print(ascii_board(puzzle, state))
        if state.standing and state.cells[0] == puzzle.goal:
            print("Solved.")
            return
        raw = input("Move> ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return
        if raw == "u":
            if history:
                state = history.pop()
                moves.pop()
            continue
        if raw == "r":
            state = puzzle.start
            history.clear()
            moves.clear()
            continue
        move = MOVE_ALIASES.get(raw)
        if move is None:
            print("Unknown move.")
            continue
        nxt = move_pose(state, move)
        if not valid(puzzle.board, nxt):
            print("Illegal move: the block would touch a missing tile or leave the board.")
            continue
        history.append(state)
        moves.append(move)
        state = nxt


def generate_puzzle(seed: int, want_reachable: bool = True) -> Puzzle:
    return sample_puzzle(random.Random(seed), want_reachable=want_reachable)


def write_jsonl(rows: Sequence[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")

    play_cmd = sub.add_parser("play", help="play a terminal puzzle")
    play_cmd.add_argument("--seed", type=int, default=20260523)
    play_cmd.add_argument("--reachable", action="store_true", help="force a solvable instance")
    play_cmd.add_argument("--unreachable", action="store_true", help="force an unsolvable instance")

    render_cmd = sub.add_parser("render", help="render a PNG for a sampled puzzle")
    render_cmd.add_argument("--seed", type=int, default=20260523)
    render_cmd.add_argument("--reachable", action="store_true", help="force a solvable instance")
    render_cmd.add_argument("--unreachable", action="store_true", help="force an unsolvable instance")
    render_cmd.add_argument("--output", type=Path, default=Path("flip_blocks.png"))

    sample_cmd = sub.add_parser("sample", help="print a sampled puzzle as JSON")
    sample_cmd.add_argument("--seed", type=int, default=20260523)
    sample_cmd.add_argument("--reachable", action="store_true", help="force a solvable instance")
    sample_cmd.add_argument("--unreachable", action="store_true", help="force an unsolvable instance")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    want_reachable = True
    if getattr(args, "unreachable", False):
        want_reachable = False
    elif getattr(args, "reachable", False):
        want_reachable = True

    if args.command == "play":
        play(generate_puzzle(args.seed, want_reachable=want_reachable))
    elif args.command == "render":
        puzzle = generate_puzzle(args.seed, want_reachable=want_reachable)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        render_puzzle(puzzle, args.output)
        print(args.output)
    elif args.command == "sample":
        puzzle = generate_puzzle(args.seed, want_reachable=want_reachable)
        print(
            json.dumps(
                {
                    "rows": puzzle.rows,
                    "cols": puzzle.cols,
                    "board": list(puzzle.board),
                    "start": list(map(list, puzzle.start.cells)),
                    "goal": list(puzzle.goal),
                    "min_steps": puzzle.min_steps,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
