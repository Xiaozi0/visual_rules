#!/usr/bin/env python3
"""SpongeBob-style rolling cube puzzle.

This file contains a complete six-face cube state model, an interactive GUI
game, a small playable terminal game, and a deterministic VQA/image sample
generator.

Directions:
  W / up    = roll north, toward smaller row index
  S / down  = roll south, toward larger row index
  A / left  = roll west, toward smaller column index
  D / right = roll east, toward larger column index
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
from pathlib import Path
from typing import Iterable, Literal

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib_cache"))

Face = Literal["face", "pants", "shirt", "back", "left", "right"]
Direction = Literal["top", "bottom", "north", "south", "west", "east"]
Move = Literal["N", "S", "W", "E"]

MOVE_ALIASES: dict[str, Move] = {
    "w": "N",
    "up": "N",
    "n": "N",
    "north": "N",
    "s": "S",
    "down": "S",
    "south": "S",
    "a": "W",
    "left": "W",
    "l": "W",
    "west": "W",
    "d": "E",
    "right": "E",
    "r": "E",
    "e": "E",
    "east": "E",
}
MOVE_LABEL = {"N": "north", "S": "south", "W": "west", "E": "east"}
MOVE_DELTA: dict[Move, tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "W": (0, -1),
    "E": (0, 1),
}

FACE_LABELS: dict[Face, str] = {
    "face": "Face",
    "pants": "Pants",
    "shirt": "Shirt",
    "back": "Back",
    "left": "Left side",
    "right": "Right side",
}
FACE_COLORS: dict[Face, str] = {
    "face": "#f4d84d",
    "pants": "#9b4f12",
    "shirt": "#f7f7ef",
    "back": "#d8cb51",
    "left": "#f0ce43",
    "right": "#e7c73e",
}


@dataclasses.dataclass(frozen=True)
class CubeState:
    """Position plus full orientation of all six cube faces.

    Direction names are board-relative:
      north = upper side in the rendered board
      south = lower side in the rendered board
      west/east = left/right side in the rendered board
    """

    row: int
    col: int
    orientation: dict[Direction, Face]

    @staticmethod
    def default(row: int = 0, col: int = 0) -> "CubeState":
        return CubeState(
            row=row,
            col=col,
            orientation={
                "top": "face",
                "bottom": "shirt",
                "north": "back",
                "south": "pants",
                "west": "left",
                "east": "right",
            },
        )

    def roll(self, move: Move) -> "CubeState":
        """Return the state after one legal geometric roll.

        Example for an east/right roll:
          old west face becomes new top
          old top face becomes new east face
          old east face becomes new bottom
          old bottom face becomes new west face
        """
        dr, dc = MOVE_DELTA[move]
        old = self.orientation

        if move == "N":
            new = {
                "top": old["south"],
                "bottom": old["north"],
                "north": old["top"],
                "south": old["bottom"],
                "west": old["west"],
                "east": old["east"],
            }
        elif move == "S":
            new = {
                "top": old["north"],
                "bottom": old["south"],
                "north": old["bottom"],
                "south": old["top"],
                "west": old["west"],
                "east": old["east"],
            }
        elif move == "W":
            new = {
                "top": old["east"],
                "bottom": old["west"],
                "north": old["north"],
                "south": old["south"],
                "west": old["top"],
                "east": old["bottom"],
            }
        else:
            new = {
                "top": old["west"],
                "bottom": old["east"],
                "north": old["north"],
                "south": old["south"],
                "west": old["bottom"],
                "east": old["top"],
            }

        return CubeState(self.row + dr, self.col + dc, new)

    def visible_faces(self) -> dict[str, Face]:
        return {
            "top": self.orientation["top"],
            "front/south": self.orientation["south"],
            "right/east": self.orientation["east"],
        }


@dataclasses.dataclass(frozen=True)
class Puzzle:
    rows: int
    cols: int
    start: CubeState
    moves: list[Move]
    goal_cell: tuple[int, int]
    goal_top: Face

    def states(self) -> list[CubeState]:
        states = [self.start]
        state = self.start
        for move in self.moves:
            state = state.roll(move)
            states.append(state)
        return states

    def final_state(self) -> CubeState:
        return self.states()[-1]

    def is_goal_reached(self) -> bool:
        final = self.final_state()
        return (final.row, final.col) == self.goal_cell and final.orientation["top"] == self.goal_top


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")

    gui = sub.add_parser("gui", help="play the interactive GUI game")
    gui.add_argument("--rows", type=int, default=4)
    gui.add_argument("--cols", type=int, default=4)
    gui.add_argument("--seed", type=int, default=17)

    play = sub.add_parser("play", help="play the puzzle in the terminal")
    play.add_argument("--rows", type=int, default=4)
    play.add_argument("--cols", type=int, default=4)
    play.add_argument("--goal-row", type=int, default=2)
    play.add_argument("--goal-col", type=int, default=2)
    play.add_argument("--goal-top", choices=sorted(FACE_LABELS), default="face")

    render = sub.add_parser("render", help="render one puzzle image")
    render.add_argument("--moves", default="E,S,W", help="comma-separated moves, e.g. E,S,W,N")
    render.add_argument("--output", type=Path, default=Path("script/puzzle_001.png"))

    gen = sub.add_parser("generate-vqa", help="generate one VQA sample and image")
    gen.add_argument("--output-dir", type=Path, default=Path("script"))
    gen.add_argument("--seed", type=int, default=7)

    args = parser.parse_args()
    if args.command in {None, "gui"}:
        launch_gui(args.rows if args.command else 4, args.cols if args.command else 4, args.seed if args.command else 17)
    elif args.command == "play":
        play_game(args.rows, args.cols, (args.goal_row, args.goal_col), args.goal_top)
    elif args.command == "render":
        puzzle = demo_puzzle(parse_moves(args.moves))
        render_puzzle(puzzle, args.output)
        print(f"Image written to {args.output}")
    elif args.command == "generate-vqa":
        generate_vqa(args.output_dir, args.seed)
    else:
        parser.print_help()


class RollingCubeGame:
    def __init__(self, rows: int, cols: int, seed: int) -> None:
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self.start = CubeState.default(row=rows // 2, col=cols // 2)
        self.state = self.start
        self.goal_cell = (0, 0)
        self.goal_top: Face = "face"
        self.history: list[CubeState] = []
        self.moves: list[Move] = []
        self.new_puzzle()

    def new_puzzle(self) -> None:
        self.start = CubeState.default(row=self.rows // 2, col=self.cols // 2)
        self.state = self.start
        self.history = []
        self.moves = []
        solution = random_legal_moves(self.rows, self.cols, self.start.row, self.start.col, 4, self.rng)
        final = apply_moves(self.start, solution)
        self.goal_cell = (final.row, final.col)
        self.goal_top = final.orientation["top"]

    def reset(self) -> None:
        self.state = self.start
        self.history = []
        self.moves = []

    def undo(self) -> None:
        if not self.history:
            return
        self.state = self.history.pop()
        self.moves.pop()

    def move(self, move: Move) -> bool:
        next_state = self.state.roll(move)
        if not inside_board(self.rows, self.cols, next_state):
            return False
        self.history.append(self.state)
        self.moves.append(move)
        self.state = next_state
        return True

    def won(self) -> bool:
        return (self.state.row, self.state.col) == self.goal_cell and self.state.orientation["top"] == self.goal_top


def launch_gui(rows: int = 4, cols: int = 4, seed: int = 17) -> None:
    import tkinter as tk
    from tkinter import ttk

    game = RollingCubeGame(rows, cols, seed)
    root = tk.Tk()
    root.title("Rolling Cube Orientation Game")
    root.geometry("1060x720")
    root.minsize(980, 660)

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=8)
    style.configure("Title.TLabel", font=("Helvetica", 18, "bold"))
    style.configure("Info.TLabel", font=("Helvetica", 12))

    outer = ttk.Frame(root, padding=16)
    outer.pack(fill="both", expand=True)

    left = ttk.Frame(outer)
    left.pack(side="left", fill="both", expand=True)
    right = ttk.Frame(outer, width=300)
    right.pack(side="right", fill="y", padx=(16, 0))

    canvas = tk.Canvas(left, width=700, height=650, bg="#f2f0e9", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    ttk.Label(right, text="Rolling Cube", style="Title.TLabel").pack(anchor="w")
    status_var = tk.StringVar()
    goal_var = tk.StringVar()
    pos_var = tk.StringVar()
    top_var = tk.StringVar()
    visible_var = tk.StringVar()
    hidden_var = tk.StringVar()
    moves_var = tk.StringVar()
    ttk.Label(right, textvariable=goal_var, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=(14, 4))
    ttk.Label(right, textvariable=status_var, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=(0, 10))
    ttk.Label(right, textvariable=pos_var, style="Info.TLabel").pack(anchor="w", pady=2)
    ttk.Label(right, textvariable=top_var, style="Info.TLabel").pack(anchor="w", pady=2)
    ttk.Label(right, textvariable=visible_var, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=8)
    ttk.Label(right, textvariable=hidden_var, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=8)
    ttk.Label(right, textvariable=moves_var, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=8)

    controls = ttk.Frame(right)
    controls.pack(pady=18)
    ttk.Button(controls, text="↑", width=5, command=lambda: do_move("N")).grid(row=0, column=1, padx=3, pady=3)
    ttk.Button(controls, text="←", width=5, command=lambda: do_move("W")).grid(row=1, column=0, padx=3, pady=3)
    ttk.Button(controls, text="↓", width=5, command=lambda: do_move("S")).grid(row=1, column=1, padx=3, pady=3)
    ttk.Button(controls, text="→", width=5, command=lambda: do_move("E")).grid(row=1, column=2, padx=3, pady=3)

    actions = ttk.Frame(right)
    actions.pack(fill="x", pady=(4, 0))
    ttk.Button(actions, text="Undo", command=lambda: (game.undo(), redraw("Undid one move."))).pack(fill="x", pady=3)
    ttk.Button(actions, text="Reset", command=lambda: (game.reset(), redraw("Reset to start."))).pack(fill="x", pady=3)
    ttk.Button(actions, text="New Puzzle", command=lambda: (game.new_puzzle(), redraw("New puzzle."))).pack(fill="x", pady=3)

    help_text = (
        "Keyboard: W/A/S/D or arrow keys.\n"
        "Win condition: stand on the red goal cell with the required top face."
    )
    ttk.Label(right, text=help_text, style="Info.TLabel", wraplength=290).pack(anchor="w", pady=(20, 0))

    def do_move(move: Move) -> None:
        ok = game.move(move)
        if not ok:
            redraw("Illegal move: the cube would leave the board.")
        elif game.won():
            redraw("Goal reached.")
        else:
            redraw(f"Rolled {MOVE_LABEL[move]}.")

    def redraw(message: str = "") -> None:
        draw_gui_scene(canvas, game)
        goal_var.set(f"Goal: reach red cell {game.goal_cell} with top face = {FACE_LABELS[game.goal_top]}.")
        pos_var.set(f"Position: row {game.state.row}, col {game.state.col}")
        top_var.set(f"Top face: {FACE_LABELS[game.state.orientation['top']]}")
        visible_var.set(
            "Visible faces: "
            f"top={FACE_LABELS[game.state.orientation['top']]}, "
            f"front={FACE_LABELS[game.state.orientation['south']]}, "
            f"right={FACE_LABELS[game.state.orientation['east']]}"
        )
        hidden_var.set(
            "Hidden/other faces: "
            f"bottom={FACE_LABELS[game.state.orientation['bottom']]}, "
            f"back={FACE_LABELS[game.state.orientation['north']]}, "
            f"left={FACE_LABELS[game.state.orientation['west']]}"
        )
        moves_var.set("Moves: " + (" ".join(MOVE_LABEL[m] for m in game.moves) if game.moves else "(none)"))
        if game.won():
            status_var.set("Status: solved.")
        else:
            status_var.set(f"Status: {message or 'playing'}")

    def on_key(event) -> None:
        key = event.keysym.lower()
        mapping = {
            "up": "N",
            "w": "N",
            "down": "S",
            "s": "S",
            "left": "W",
            "a": "W",
            "right": "E",
            "d": "E",
        }
        move = mapping.get(key)
        if move:
            do_move(move)  # type: ignore[arg-type]

    root.bind("<Key>", on_key)
    redraw("playing")
    root.mainloop()


def draw_gui_scene(canvas, game: RollingCubeGame) -> None:
    canvas.delete("all")
    width = max(canvas.winfo_width(), 700)
    height = max(canvas.winfo_height(), 620)
    cell = min((width - 120) / game.cols, (height - 130) / game.rows, 112)
    board_w = cell * game.cols
    board_h = cell * game.rows
    x0 = (width - board_w) / 2
    y0 = 74

    canvas.create_text(
        width / 2,
        28,
        text="Move the cube. Match the red cell and the required top face.",
        font=("Helvetica", 17, "bold"),
        fill="#242424",
    )

    for row in range(game.rows):
        for col in range(game.cols):
            x = x0 + col * cell
            y = y0 + row * cell
            fill = "#f7f7f2" if (row + col) % 2 == 0 else "#303234"
            outline = "#7c7a72"
            canvas.create_rectangle(x, y, x + cell, y + cell, fill=fill, outline=outline, width=2)
            if (row, col) == game.goal_cell:
                canvas.create_rectangle(x + 7, y + 7, x + cell - 7, y + cell - 7, outline="#e34b3f", width=5)
                canvas.create_text(x + cell / 2, y + cell - 17, text="GOAL", fill="#e34b3f", font=("Helvetica", 11, "bold"))

    draw_gui_cube(canvas, game.state, x0, y0, cell)

    legend_y = y0 + board_h + 28
    canvas.create_text(x0, legend_y, anchor="w", text="Face legend:", font=("Helvetica", 13, "bold"), fill="#242424")
    lx = x0 + 105
    for face in ["face", "pants", "shirt", "back", "left", "right"]:
        canvas.create_rectangle(lx, legend_y - 12, lx + 18, legend_y + 6, fill=FACE_COLORS[face], outline="#333333")
        canvas.create_text(lx + 24, legend_y - 3, anchor="w", text=FACE_LABELS[face], font=("Helvetica", 11), fill="#222222")
        lx += 96


def draw_gui_cube(canvas, state: CubeState, board_x: float, board_y: float, cell: float) -> None:
    cx = board_x + state.col * cell + cell / 2
    cy = board_y + state.row * cell + cell / 2 + 12
    scale = cell / 104
    w = 44 * scale
    h = 34 * scale
    top = [(cx, cy - h - 26 * scale), (cx + w, cy - h), (cx, cy + 26 * scale), (cx - w, cy - h)]
    left = [(cx - w, cy - h), (cx, cy + 26 * scale), (cx, cy + h + 42 * scale), (cx - w, cy + 16 * scale)]
    right = [(cx + w, cy - h), (cx, cy + 26 * scale), (cx, cy + h + 42 * scale), (cx + w, cy + 16 * scale)]

    for direction, poly in [("south", left), ("east", right), ("top", top)]:
        face = state.orientation[direction]  # type: ignore[index]
        canvas.create_polygon(poly, fill=FACE_COLORS[face], outline="#151515", width=3)
        draw_face_mark(canvas, poly, face)


def draw_face_mark(canvas, poly: list[tuple[float, float]], face: Face) -> None:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    label = FACE_LABELS[face]
    if face == "face":
        r = 4
        canvas.create_oval(cx - 15, cy - 9, cx - 7, cy - 1, fill="#ffffff", outline="#222222")
        canvas.create_oval(cx + 7, cy - 9, cx + 15, cy - 1, fill="#ffffff", outline="#222222")
        canvas.create_oval(cx - 11, cy - 6, cx - 8, cy - 3, fill="#1c6aa6", outline="")
        canvas.create_oval(cx + 10, cy - 6, cx + 13, cy - 3, fill="#1c6aa6", outline="")
        canvas.create_arc(cx - 15, cy - 2, cx + 15, cy + 16, start=200, extent=140, style="arc", width=2)
        canvas.create_text(cx, cy + 28, text="Face", font=("Helvetica", 10, "bold"), fill="#171717")
    elif face == "pants":
        canvas.create_rectangle(cx - 25, cy - 8, cx + 25, cy + 13, fill="#9b4f12", outline="#5a2c0a")
        canvas.create_line(cx - 25, cy, cx + 25, cy, fill="#222222", dash=(3, 3))
        canvas.create_text(cx, cy + 28, text="Pants", font=("Helvetica", 10, "bold"), fill="#171717")
    elif face == "shirt":
        canvas.create_rectangle(cx - 25, cy - 10, cx + 25, cy + 12, fill="#ffffff", outline="#444444")
        canvas.create_polygon([(cx - 6, cy - 8), (cx, cy + 3), (cx + 6, cy - 8)], fill="#d22f2f", outline="#8a1717")
        canvas.create_text(cx, cy + 28, text="Shirt", font=("Helvetica", 10, "bold"), fill="#171717")
    else:
        canvas.create_text(cx, cy, text=label, font=("Helvetica", 10, "bold"), fill="#171717", width=70)


def play_game(rows: int, cols: int, goal_cell: tuple[int, int], goal_top: Face) -> None:
    state = CubeState.default(row=0, col=0)
    print("Rolling Cube Puzzle")
    print("Controls: W/A/S/D, or up/left/down/right. Type q to quit.")
    print(f"Goal: reach cell {goal_cell} with top face = {FACE_LABELS[goal_top]}.")

    while True:
        print_board(rows, cols, state, goal_cell)
        print_state(state)
        if (state.row, state.col) == goal_cell and state.orientation["top"] == goal_top:
            print("Goal reached.")
            return

        raw = input("Move> ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return
        move = MOVE_ALIASES.get(raw)
        if move is None:
            print("Unknown move.")
            continue
        next_state = state.roll(move)
        if not inside_board(rows, cols, next_state):
            print("Illegal move: the cube would leave the board.")
            continue
        state = next_state


def print_board(rows: int, cols: int, state: CubeState, goal_cell: tuple[int, int]) -> None:
    print()
    for r in range(rows):
        cells = []
        for c in range(cols):
            if (r, c) == (state.row, state.col):
                cells.append(" C ")
            elif (r, c) == goal_cell:
                cells.append(" G ")
            else:
                cells.append(" . ")
        print("".join(cells))


def print_state(state: CubeState) -> None:
    print(f"Position: row={state.row}, col={state.col}")
    for direction in ["top", "bottom", "north", "south", "west", "east"]:
        face = state.orientation[direction]  # type: ignore[index]
        print(f"  {direction:>6}: {FACE_LABELS[face]}")


def inside_board(rows: int, cols: int, state: CubeState) -> bool:
    return 0 <= state.row < rows and 0 <= state.col < cols


def demo_puzzle(moves: list[Move]) -> Puzzle:
    start = CubeState.default(row=1, col=1)
    final = apply_moves(start, moves)
    return Puzzle(
        rows=4,
        cols=4,
        start=start,
        moves=moves,
        goal_cell=(final.row, final.col),
        goal_top=final.orientation["top"],
    )


def parse_moves(text: str) -> list[Move]:
    moves = []
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        key = part.lower()
        move = MOVE_ALIASES.get(key)
        if move is None:
            raise ValueError(f"unknown move: {part}")
        moves.append(move)
    if not moves:
        raise ValueError("at least one move is required")
    return moves


def apply_moves(start: CubeState, moves: Iterable[Move]) -> CubeState:
    state = start
    for move in moves:
        state = state.roll(move)
    return state


def render_puzzle(puzzle: Puzzle, output: Path) -> None:
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_box_aspect([1, 1, 0.45])

    draw_board(ax, puzzle.rows, puzzle.cols, puzzle.goal_cell)
    draw_path(ax, puzzle.states())
    draw_cube(ax, puzzle.start)

    ax.set_xlim(-0.2, puzzle.cols + 0.2)
    ax.set_ylim(-0.2, puzzle.rows + 0.2)
    ax.set_zlim(0, 2.1)
    ax.view_init(elev=34, azim=-50)
    ax.axis("off")
    title = "Roll the cube along the arrows. Match both final cell and top face."
    ax.set_title(title, fontsize=13, pad=14)
    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight", dpi=150)
    plt.close()


def draw_board(ax, rows: int, cols: int, goal_cell: tuple[int, int]) -> None:
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    for row in range(rows):
        for col in range(cols):
            color = "#f0f0f0" if (row + col) % 2 == 0 else "#303030"
            if (row, col) == goal_cell:
                color = "#e44b3f"
            x = [col, col + 1, col + 1, col]
            y = [row, row, row + 1, row + 1]
            z = [0, 0, 0, 0]
            ax.add_collection3d(
                Poly3DCollection([list(zip(x, y, z))], facecolors=color, edgecolors="#555555", linewidths=1.0)
            )


def draw_path(ax, states: list[CubeState]) -> None:
    centers = [(s.col + 0.5, s.row + 0.5, 0.04) for s in states]
    for index, (a, b) in enumerate(zip(centers, centers[1:]), start=1):
        ax.quiver(
            a[0],
            a[1],
            a[2],
            b[0] - a[0],
            b[1] - a[1],
            0,
            color="#2574c7",
            arrow_length_ratio=0.22,
            linewidth=2.4,
        )
        mx = (a[0] + b[0]) / 2
        my = (a[1] + b[1]) / 2
        ax.text(mx, my, 0.1, str(index), color="#123c6d", ha="center", va="center", fontsize=10, weight="bold")


def draw_cube(ax, state: CubeState) -> None:
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    x = state.col
    y = state.row
    vertices = np.array(
        [
            [x, y, 0],
            [x + 1, y, 0],
            [x + 1, y + 1, 0],
            [x, y + 1, 0],
            [x, y, 1],
            [x + 1, y, 1],
            [x + 1, y + 1, 1],
            [x, y + 1, 1],
        ]
    )
    face_vertices = {
        "bottom": [vertices[i] for i in [0, 1, 2, 3]],
        "top": [vertices[i] for i in [4, 5, 6, 7]],
        "north": [vertices[i] for i in [0, 1, 5, 4]],
        "south": [vertices[i] for i in [2, 3, 7, 6]],
        "west": [vertices[i] for i in [0, 3, 7, 4]],
        "east": [vertices[i] for i in [1, 2, 6, 5]],
    }
    for direction, verts in face_vertices.items():
        face = state.orientation[direction]  # type: ignore[index]
        ax.add_collection3d(
            Poly3DCollection(
                [verts],
                facecolors=FACE_COLORS[face],
                edgecolors="black",
                linewidths=1.4,
                alpha=1.0,
            )
        )

    for direction in ["top", "south", "east"]:
        verts = face_vertices[direction]
        center = np.mean(verts, axis=0)
        face = state.orientation[direction]  # type: ignore[index]
        ax.text(
            center[0],
            center[1],
            center[2] + 0.04,
            FACE_LABELS[face],
            color="black",
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
        )


def generate_vqa(output_dir: Path, seed: int) -> None:
    rng = random.Random(seed)
    moves = random_legal_moves(rows=4, cols=4, start_row=1, start_col=1, length=3, rng=rng)
    puzzle = demo_puzzle(moves)
    image_path = output_dir / "puzzle_001.png"
    render_puzzle(puzzle, image_path)

    final = puzzle.final_state()
    question = (
        "<image>\n"
        "The cube starts on the blue-labeled start cell. Its six faces are Face, Pants, Shirt, "
        "Back, Left side, and Right side. Follow the numbered arrows. What face is on top at the end? "
        "Answer with one face name only."
    )
    sample = [
        {
            "id": "spongebob_cube_001",
            "image": image_path.name,
            "question": question,
            "answer": FACE_LABELS[final.orientation["top"]],
            "metadata": {
                "moves": [MOVE_LABEL[m] for m in puzzle.moves],
                "start_cell": [puzzle.start.row, puzzle.start.col],
                "goal_cell": list(puzzle.goal_cell),
                "start_orientation": orientation_labels(puzzle.start.orientation),
                "final_orientation": orientation_labels(final.orientation),
            },
        }
    ]
    json_path = output_dir / "vqa_dataset.json"
    json_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Image written to {image_path}")
    print(f"VQA JSON written to {json_path}")


def random_legal_moves(
    rows: int,
    cols: int,
    start_row: int,
    start_col: int,
    length: int,
    rng: random.Random,
) -> list[Move]:
    row = start_row
    col = start_col
    moves: list[Move] = []
    for _ in range(length):
        legal = []
        for move, (dr, dc) in MOVE_DELTA.items():
            nr = row + dr
            nc = col + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                legal.append(move)
        move = rng.choice(legal)
        dr, dc = MOVE_DELTA[move]
        row += dr
        col += dc
        moves.append(move)
    return moves


def orientation_labels(orientation: dict[Direction, Face]) -> dict[str, str]:
    return {direction: FACE_LABELS[face] for direction, face in orientation.items()}


if __name__ == "__main__":
    main()
