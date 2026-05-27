#!/usr/bin/env python3
"""SpongeBob cube-roll simulator and renderer for static VQA generation."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw


VERSION = "haimian_flip_game_v1.0.0"
GENERATOR_TAG = "codex"
CANVAS = 720
FACE_NAMES = ("head", "foot", "face", "body", "left", "right")
MOVES = ("up", "down", "left", "right")

BG = (218, 226, 235)
PANEL = (245, 249, 252)
PANEL_EDGE = (163, 176, 190)
TILE_LIGHT = (239, 243, 247)
TILE_DARK = (215, 222, 230)
GRID_EDGE = (123, 136, 149)
START_TILE = (113, 185, 109)
END_TILE = (218, 92, 83)
ARROW_BG = (255, 246, 207)
ARROW_FG = (99, 76, 28)
CARD_BG = (255, 255, 255)
CARD_EDGE = (130, 141, 154)
INK = (36, 42, 49)
SKIN = (248, 224, 82)
SKIN_DARK = (220, 193, 58)
SKIN_DEEP = (181, 154, 44)
WHITE = (249, 250, 252)
BLUE = (77, 145, 223)
BROWN = (136, 81, 39)
RED = (201, 56, 64)


def shade(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(max(0, min(255, channel + delta)) for channel in color)


@dataclass(frozen=True)
class Orientation:
    top: str
    bottom: str
    front: str
    back: str
    left: str
    right: str


@dataclass(frozen=True)
class Puzzle:
    rows: int
    cols: int
    start: tuple[int, int]
    path: tuple[str, ...]
    target_face: str
    final_top: str
    answer: str
    orientation: Orientation


def initial_orientation() -> Orientation:
    return Orientation(top="head", bottom="foot", front="face", back="body", left="left", right="right")


def roll(orientation: Orientation, move: str) -> Orientation:
    if move == "right":
        return Orientation(
            top=orientation.left,
            bottom=orientation.right,
            front=orientation.front,
            back=orientation.back,
            left=orientation.bottom,
            right=orientation.top,
        )
    if move == "left":
        return Orientation(
            top=orientation.right,
            bottom=orientation.left,
            front=orientation.front,
            back=orientation.back,
            left=orientation.top,
            right=orientation.bottom,
        )
    if move == "up":
        return Orientation(
            top=orientation.front,
            bottom=orientation.back,
            front=orientation.bottom,
            back=orientation.top,
            left=orientation.left,
            right=orientation.right,
        )
    if move == "down":
        return Orientation(
            top=orientation.back,
            bottom=orientation.front,
            front=orientation.top,
            back=orientation.bottom,
            left=orientation.left,
            right=orientation.right,
        )
    raise ValueError(move)


def move_pos(pos: tuple[int, int], move: str) -> tuple[int, int]:
    row, col = pos
    if move == "up":
        return (row - 1, col)
    if move == "down":
        return (row + 1, col)
    if move == "left":
        return (row, col - 1)
    if move == "right":
        return (row, col + 1)
    raise ValueError(move)


def simulate(start: tuple[int, int], path: Sequence[str], orientation: Orientation | None = None) -> tuple[tuple[int, int], Orientation]:
    current = orientation or initial_orientation()
    pos = start
    for move in path:
        pos = move_pos(pos, move)
        current = roll(current, move)
    return pos, current


def sample_path(rng: random.Random, rows: int, cols: int, length: int) -> tuple[tuple[int, int], tuple[str, ...]]:
    for _ in range(400):
        start = (rng.randrange(1, rows - 1), rng.randrange(1, cols - 1))
        pos = start
        path: list[str] = []
        for _step in range(length):
            candidates = []
            for move in MOVES:
                nxt = move_pos(pos, move)
                if 0 <= nxt[0] < rows and 0 <= nxt[1] < cols:
                    candidates.append((move, nxt))
            if not candidates:
                break
            move, nxt = rng.choice(candidates)
            path.append(move)
            pos = nxt
        if len(path) == length and pos != start:
            return start, tuple(path)
    raise RuntimeError("failed to sample a valid path")


def generate_puzzle(seed: int, *, force_answer: bool | None = None) -> Puzzle:
    rng = random.Random(seed)
    rows = rng.randint(5, 6)
    cols = rng.randint(5, 6)
    length = rng.randint(4, 6)
    start, path = sample_path(rng, rows, cols, length)
    _, final_orientation = simulate(start, path)
    final_top = final_orientation.top
    if force_answer is None:
        use_true_answer = rng.choice([True, False])
    else:
        use_true_answer = force_answer
    if use_true_answer:
        target_face = final_top
    else:
        target_face = rng.choice([name for name in FACE_NAMES if name != final_top])
    answer = "yes" if target_face == final_top else "no"
    return Puzzle(
        rows=rows,
        cols=cols,
        start=start,
        path=path,
        target_face=target_face,
        final_top=final_top,
        answer=answer,
        orientation=initial_orientation(),
    )


def face_palette(face_name: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if face_name == "head":
        return (SKIN, (246, 242, 224))
    if face_name == "foot":
        return ((244, 239, 230), BROWN)
    if face_name == "face":
        return (SKIN, WHITE)
    if face_name == "body":
        return (SKIN_DARK, SKIN_DEEP)
    if face_name == "left":
        return (SKIN, BLUE)
    if face_name == "right":
        return (SKIN, RED)
    raise ValueError(face_name)


def draw_face_icon(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], face_name: str) -> None:
    x0, y0, x1, y1 = box
    fill, accent = face_palette(face_name)
    draw.rounded_rectangle(box, radius=12, fill=fill, outline=INK, width=3)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    w = x1 - x0
    h = y1 - y0
    if face_name == "face":
        draw.ellipse((cx - w * 0.19, cy - h * 0.18, cx - w * 0.03, cy), fill=WHITE, outline=INK, width=2)
        draw.ellipse((cx + w * 0.03, cy - h * 0.18, cx + w * 0.19, cy), fill=WHITE, outline=INK, width=2)
        draw.ellipse((cx - w * 0.13, cy - h * 0.11, cx - w * 0.07, cy - h * 0.02), fill=BLUE)
        draw.ellipse((cx + w * 0.07, cy - h * 0.11, cx + w * 0.13, cy - h * 0.02), fill=BLUE)
        draw.arc((cx - w * 0.20, cy - h * 0.01, cx + w * 0.20, cy + h * 0.23), start=15, end=165, fill=INK, width=3)
        for dx, dy, rr in ((-0.22, 0.23, 0.05), (0.19, 0.12, 0.06), (-0.16, -0.23, 0.04)):
            draw.ellipse((cx + w * dx - w * rr, cy + h * dy - h * rr, cx + w * dx + w * rr, cy + h * dy + h * rr), fill=SKIN_DARK)
    elif face_name == "body":
        for ox in (-0.22, 0.0, 0.22):
            draw.ellipse((cx + w * ox - 10, cy - 12, cx + w * ox + 10, cy + 8), fill=accent, outline=INK, width=2)
        draw.rectangle((cx - w * 0.22, cy + h * 0.18, cx + w * 0.22, cy + h * 0.30), fill=WHITE, outline=INK, width=2)
        draw.rectangle((cx - w * 0.18, cy + h * 0.30, cx + w * 0.18, cy + h * 0.44), fill=BROWN, outline=INK, width=2)
    elif face_name == "head":
        draw.arc((cx - w * 0.22, cy - h * 0.26, cx + w * 0.22, cy + h * 0.08), start=195, end=345, fill=INK, width=4)
        draw.line((cx - w * 0.16, cy - h * 0.03, cx + w * 0.16, cy - h * 0.03), fill=RED, width=4)
        draw.line((cx, cy - h * 0.03, cx, cy + h * 0.22), fill=RED, width=4)
    elif face_name == "foot":
        draw.rectangle((cx - w * 0.25, cy + h * 0.10, cx - w * 0.04, cy + h * 0.26), fill=BROWN, outline=INK, width=2)
        draw.rectangle((cx + w * 0.04, cy + h * 0.10, cx + w * 0.25, cy + h * 0.26), fill=BROWN, outline=INK, width=2)
        draw.line((cx - w * 0.12, cy - h * 0.20, cx - w * 0.12, cy + h * 0.08), fill=INK, width=3)
        draw.line((cx + w * 0.12, cy - h * 0.20, cx + w * 0.12, cy + h * 0.08), fill=INK, width=3)
    elif face_name == "left":
        draw.arc((cx - w * 0.28, cy - h * 0.20, cx + w * 0.05, cy + h * 0.18), start=245, end=55, fill=accent, width=9)
        draw.ellipse((cx - w * 0.03, cy + h * 0.02, cx + w * 0.13, cy + h * 0.18), fill=accent, outline=INK, width=2)
    elif face_name == "right":
        draw.arc((cx - w * 0.05, cy - h * 0.20, cx + w * 0.28, cy + h * 0.18), start=125, end=295, fill=accent, width=9)
        draw.ellipse((cx - w * 0.13, cy + h * 0.02, cx + w * 0.03, cy + h * 0.18), fill=accent, outline=INK, width=2)


def _tile_box(origin_x: int, origin_y: int, cell: int, row: int, col: int) -> tuple[int, int, int, int]:
    x0 = origin_x + col * cell
    y0 = origin_y + row * cell
    return (x0, y0, x0 + cell, y0 + cell)


def iso_point(origin_x: float, origin_y: float, row: float, col: float, tile_w: float, tile_h: float) -> tuple[float, float]:
    return (origin_x + (col - row) * tile_w / 2, origin_y + (col + row) * tile_h / 2)


def tile_poly(origin_x: float, origin_y: float, row: float, col: float, tile_w: float, tile_h: float) -> list[tuple[float, float]]:
    cx, cy = iso_point(origin_x, origin_y, row, col, tile_w, tile_h)
    return [(cx, cy - tile_h / 2), (cx + tile_w / 2, cy), (cx, cy + tile_h / 2), (cx - tile_w / 2, cy)]


def draw_prism(
    draw: ImageDraw.ImageDraw,
    top: list[tuple[float, float]],
    *,
    height: float,
    top_fill: tuple[int, int, int],
    left_fill: tuple[int, int, int],
    right_fill: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> None:
    lowered = [(x, y + height) for x, y in top]
    left = [top[3], top[2], lowered[2], lowered[3]]
    right = [top[1], top[2], lowered[2], lowered[1]]
    draw.polygon(left, fill=left_fill, outline=outline)
    draw.polygon(right, fill=right_fill, outline=outline)
    draw.polygon(top, fill=top_fill, outline=outline)


def _arrow_points(move: str, box: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    if move == "up":
        return [(cx, y0 + 12), (cx + 16, cy + 10), (cx + 5, cy + 10), (cx + 5, y1 - 12), (cx - 5, y1 - 12), (cx - 5, cy + 10), (cx - 16, cy + 10)]
    if move == "down":
        return [(cx, y1 - 12), (cx + 16, cy - 10), (cx + 5, cy - 10), (cx + 5, y0 + 12), (cx - 5, y0 + 12), (cx - 5, cy - 10), (cx - 16, cy - 10)]
    if move == "left":
        return [(x0 + 12, cy), (cx + 10, cy - 16), (cx + 10, cy - 5), (x1 - 12, cy - 5), (x1 - 12, cy + 5), (cx + 10, cy + 5), (cx + 10, cy + 16)]
    if move == "right":
        return [(x1 - 12, cy), (cx - 10, cy - 16), (cx - 10, cy - 5), (x0 + 12, cy - 5), (x0 + 12, cy + 5), (cx - 10, cy + 5), (cx - 10, cy + 16)]
    raise ValueError(move)


def _draw_cube(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], orientation: Orientation) -> None:
    x0, y0, x1, y1 = box
    front = (x0 + 18, y0 + 28, x1 - 10, y1 - 6)
    top = [(x0 + 18, y0 + 28), (x0 + 36, y0 + 10), (x1 - 10, y0 + 10), (x1 - 28, y0 + 28)]
    side = [(x1 - 10, y0 + 28), (x1 - 28, y0 + 10), (x1 - 28, y1 - 24), (x1 - 10, y1 - 6)]
    draw.polygon(top, fill=face_palette(orientation.top)[0], outline=INK)
    draw.polygon(side, fill=SKIN_DARK, outline=INK)
    draw.rounded_rectangle(front, radius=10, fill=face_palette(orientation.front)[0], outline=INK, width=3)
    draw_face_icon(draw, front, orientation.front)
    side_box = (x1 - 38, y0 + 22, x1 - 14, y1 - 18)
    draw_face_icon(draw, side_box, orientation.right)
    top_box = (x0 + 32, y0 + 12, x1 - 26, y0 + 36)
    draw_face_icon(draw, top_box, orientation.top)


def draw_iso_cube(
    draw: ImageDraw.ImageDraw,
    top: list[tuple[float, float]],
    orientation: Orientation,
    *,
    height: float,
) -> None:
    lowered = [(x, y + height) for x, y in top]
    front = [top[3], top[2], lowered[2], lowered[3]]
    side = [top[1], top[2], lowered[2], lowered[1]]
    draw.polygon(front, fill=face_palette(orientation.front)[0], outline=INK)
    draw.polygon(side, fill=shade(face_palette(orientation.right)[0], -18), outline=INK)
    draw.polygon(top, fill=shade(face_palette(orientation.top)[0], 10), outline=INK)

    fx = [p[0] for p in front]
    fy = [p[1] for p in front]
    draw_face_icon(draw, (min(fx) + 10, min(fy) + 12, max(fx) - 10, max(fy) - 8), orientation.front)

    sx = [p[0] for p in side]
    sy = [p[1] for p in side]
    draw_face_icon(draw, (min(sx) + 4, min(sy) + 10, max(sx) - 4, max(sy) - 8), orientation.right)

    tx = [p[0] for p in top]
    ty = [p[1] for p in top]
    draw_face_icon(draw, (min(tx) + 14, min(ty) + 6, max(tx) - 14, max(ty) - 6), orientation.top)


def render_puzzle(puzzle: Puzzle, path: Path) -> None:
    image = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(image)
    tile_w = min(90.0, (CANVAS - 250) / max(puzzle.rows, puzzle.cols) * 1.55)
    tile_h = tile_w * 0.46
    origin_x = 276.0 + (puzzle.rows - puzzle.cols) * tile_w * 0.18
    origin_y = 142.0
    platform_depth = tile_h * 0.34

    pos = puzzle.start
    route = [pos]
    for move in puzzle.path:
        pos = move_pos(pos, move)
        route.append(pos)

    all_points = []
    for row in range(puzzle.rows):
        for col in range(puzzle.cols):
            all_points.extend(tile_poly(origin_x, origin_y, row, col, tile_w, tile_h))
    min_x = min(x for x, _ in all_points)
    max_x = max(x for x, _ in all_points)
    min_y = min(y for _, y in all_points)
    max_y = max(y for _, y in all_points) + tile_h * 3.2
    origin_x += (516 - (max_x - min_x)) / 2 - min_x
    origin_y += (576 - (max_y - min_y)) / 2 - min_y + 22

    board_panel = (36, 74, 530, 602)
    draw.rounded_rectangle(board_panel, radius=28, fill=PANEL, outline=PANEL_EDGE, width=3)

    for row in range(puzzle.rows):
        for col in range(puzzle.cols):
            poly = tile_poly(origin_x, origin_y, row, col, tile_w, tile_h)
            fill = TILE_LIGHT if (row + col) % 2 == 0 else TILE_DARK
            if (row, col) == puzzle.start:
                fill = START_TILE
            elif (row, col) == route[-1]:
                fill = END_TILE
            draw_prism(
                draw,
                poly,
                height=platform_depth,
                top_fill=fill,
                left_fill=shade(fill, -26),
                right_fill=shade(fill, -12),
                outline=GRID_EDGE,
            )

    for step, move in enumerate(puzzle.path):
        row, col = route[step]
        poly = tile_poly(origin_x, origin_y, row, col, tile_w, tile_h)
        cx = sum(x for x, _ in poly) / 4
        cy = sum(y for _, y in poly) / 4 + platform_depth * 0.28
        marker = (cx - tile_w * 0.18, cy - tile_h * 0.28, cx + tile_w * 0.18, cy + tile_h * 0.28)
        draw.rounded_rectangle(marker, radius=10, fill=ARROW_BG, outline=(208, 191, 130), width=2)
        draw.polygon(_arrow_points(move, (int(marker[0]), int(marker[1]), int(marker[2]), int(marker[3]))), fill=ARROW_FG)

    start_top = tile_poly(origin_x, origin_y, puzzle.start[0], puzzle.start[1], tile_w, tile_h)
    draw_iso_cube(draw, start_top, puzzle.orientation, height=tile_h * 1.95)

    card_box = (554, 112, 678, 236)
    draw.rounded_rectangle(card_box, radius=18, fill=CARD_BG, outline=CARD_EDGE, width=3)
    draw_face_icon(draw, (card_box[0] + 18, card_box[1] + 18, card_box[2] - 18, card_box[3] - 18), puzzle.target_face)

    icon_box = (554, 278, 678, 402)
    draw.rounded_rectangle(icon_box, radius=18, fill=CARD_BG, outline=CARD_EDGE, width=3)
    draw_face_icon(draw, (icon_box[0] + 18, icon_box[1] + 18, icon_box[2] - 18, icon_box[3] - 18), puzzle.orientation.top)

    image.save(path)


def puzzle_to_dict(puzzle: Puzzle) -> dict:
    return {
        "rows": puzzle.rows,
        "cols": puzzle.cols,
        "start": list(puzzle.start),
        "path": list(puzzle.path),
        "target_face": puzzle.target_face,
        "final_top": puzzle.final_top,
        "answer": puzzle.answer,
        "orientation": {
            "top": puzzle.orientation.top,
            "bottom": puzzle.orientation.bottom,
            "front": puzzle.orientation.front,
            "back": puzzle.orientation.back,
            "left": puzzle.orientation.left,
            "right": puzzle.orientation.right,
        },
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
