#!/usr/bin/env python3
"""Generate deterministic VQA samples for Sliding Puzzle."""

from __future__ import annotations

import argparse, json, random
from pathlib import Path
from typing import Dict, List, Sequence, Tuple
from PIL import Image, ImageDraw, ImageFont

VERSION = "sliding_puzzle_v1.0.0"
SCRIPT_NAME = "sliding_puzzle_vqa_generator.py"
CANVAS = 600
N = 4
CELL = CANVAS // N
BLANK = 0
RULE_SOURCE = "original/批次 5-0521.md:Sliding Puzzle; vendor/sliding_puzzle/slidepuzzle.py"


def solved_board() -> List[List[int]]:
    vals = list(range(1, 16)) + [BLANK]
    return [vals[r * N:(r + 1) * N] for r in range(N)]


def blank_pos(board: List[List[int]]) -> Tuple[int, int]:
    for r in range(N):
        for c in range(N):
            if board[r][c] == BLANK:
                return r, c
    raise ValueError("blank missing")


def neighbors(board: List[List[int]]) -> List[int]:
    r, c = blank_pos(board)
    vals = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            vals.append(board[rr][cc])
    return sorted(vals)


def legal_tile(board: List[List[int]], tile: int) -> bool:
    return tile in neighbors(board)


def move_blank_with_tile(board: List[List[int]], tile: int) -> List[List[int]]:
    if not legal_tile(board, tile):
        raise ValueError("illegal move")
    out = [row[:] for row in board]
    br, bc = blank_pos(out)
    for r in range(N):
        for c in range(N):
            if out[r][c] == tile:
                out[br][bc], out[r][c] = out[r][c], out[br][bc]
                return out
    raise ValueError("tile missing")


def scramble(rng: random.Random, steps: int = 18) -> List[List[int]]:
    board = solved_board()
    prev = None
    for _ in range(steps):
        opts = [x for x in neighbors(board) if x != prev]
        tile = rng.choice(opts)
        board = move_blank_with_tile(board, tile)
        prev = tile
    return board


def render(board: List[List[int]], path: Path, candidate_tile: int | None = None) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), (34, 38, 48))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    for r in range(N):
        for c in range(N):
            x0, y0 = c * CELL + 12, r * CELL + 12
            x1, y1 = (c + 1) * CELL - 12, (r + 1) * CELL - 12
            val = board[r][c]
            if val == BLANK:
                draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=(25, 29, 38), outline=(232, 235, 241), width=4)
            else:
                outline = (255, 205, 92) if val == candidate_tile else (74, 88, 114)
                width = 7 if val == candidate_tile else 3
                draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=(226, 232, 242), outline=outline, width=width)
                text = str(val)
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2), text, fill=(22, 28, 38), font=font)
    img.save(path)


def build_state(rng: random.Random, kind: str) -> Dict:
    board = scramble(rng)
    if kind == "blank_neighbors":
        return {"kind": kind, "board": board, "candidate_tile": None}
    legal = set(neighbors(board))
    want_legal = rng.choice([True, False])
    pool = sorted(legal) if want_legal else [x for x in range(1, 16) if x not in legal]
    candidate = rng.choice(pool)
    return {"kind": kind, "board": board, "candidate_tile": candidate}


def solve(state: Dict) -> str:
    if state["kind"] == "blank_neighbors":
        return ", ".join(str(x) for x in neighbors(state["board"]))
    return "yes" if legal_tile(state["board"], state["candidate_tile"]) else "no"


def record(idx: int, seed: int, state: Dict, answer: str, media: str) -> Dict:
    if state["kind"] == "blank_neighbors":
        q = "<image> This is a 4 by 4 sliding puzzle. The dark empty square is the blank. Which numbered tiles can legally slide into the blank in one move? Answer with the tile numbers in ascending order, separated by commas."
        choices, atype, diff, score = [], "list", "medium", 0.45
    else:
        q = f"<image> This is a 4 by 4 sliding puzzle. The yellow-outlined tile is {state['candidate_tile']}. Can this tile legally slide into the blank in one move? Answer only yes or no."
        choices, atype, diff, score = ["yes", "no"], "yes_no", "easy", 0.3
    return {"id": f"r_sliding_puzzle_v1-{seed}-{idx:05d}", "media": [media], "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}], "metadata": {"classification": {"domain": "games", "task": "sliding_puzzle_legal_moves", "reasoning_type": "algorithmic", "visual_type": "grid_board", "rule_delivery_mode": "explicit_text_prompt"}, "dataset": {"slug": "sliding_puzzle_v1", "version": VERSION}, "provenance": {"source": "https://inventwithpython.com/blog/i-need-practice-programming-49-ideas-for-game-clones-to-code.html#slidingpuzzle", "method": "deterministic_algorithm", "seed": seed, "index": idx, "seed_description": "4x4 board produced by legal scrambling from solved state.", "generator": f"{SCRIPT_NAME}@{VERSION}", "rule_source": RULE_SOURCE}, "gt": {"answer": answer, "answer_text": answer, "answer_type": atype, "choices": choices, "validator": {"kind": "exact_match", "solution": answer}}, "instance": {"difficulty": diff, "complexity_score": score, "reasoning_depth": 1, "visual_load": 1.0, "tags": ["sliding-puzzle", "legal-move"], "raw_state": state}}}


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
        state = build_state(random.Random(s), ["blank_neighbors", "candidate_legal"][idx % 2])
        ans = solve(state)
        img = f"images/{idx:05d}.png"
        render(state["board"], out_dir / img, state.get("candidate_tile"))
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "sliding_puzzle_v1.rule", "rule": "Only tiles orthogonally adjacent to the blank can slide into it."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": solve(r["metadata"]["instance"]["raw_state"]) == r["metadata"]["gt"]["answer"], "reason": "legal-move verifier", "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "sliding_puzzle_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "medium", "reasoning_max": "high", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "reproduce_command": f"python3 generator/{SCRIPT_NAME} --count {len(records)} --seed {seed} --out-dir {out_dir}", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(q["keep"] for q in quality):
        raise RuntimeError("quality verification failed")
    return records


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/sliding_puzzle_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Sliding Puzzle VQA records to {a.out_dir}")


if __name__ == "__main__":
    main()
