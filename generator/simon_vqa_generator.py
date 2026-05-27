#!/usr/bin/env python3
"""Generate deterministic VQA samples for Simon."""

from __future__ import annotations

import argparse, json, random
from pathlib import Path
from typing import Dict, List, Sequence
from PIL import Image, ImageDraw

VERSION = "simon_v1.0.0"
SCRIPT_NAME = "simon_vqa_generator.py"
CANVAS = 600
RULE_SOURCE = "original/批次 5-0521.md:Simon; vendor/simon/simulate.py"
COLORS = {"red": (221, 62, 70), "blue": (58, 112, 210), "green": (66, 172, 99), "yellow": (232, 194, 57)}
POSITIONS = {"red": (65, 65, 285, 285), "blue": (315, 65, 535, 285), "green": (65, 315, 285, 535), "yellow": (315, 315, 535, 535)}


def lighten(rgb):
    return tuple(min(255, int(v * 1.35 + 25)) for v in rgb)


def render(state: Dict, path: Path) -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), (24, 28, 36))
    draw = ImageDraw.Draw(img)
    for name, box in POSITIONS.items():
        active = name == state["highlight"]
        fill = lighten(COLORS[name]) if active else COLORS[name]
        outline = (255, 245, 170) if active else (42, 48, 62)
        width = 9 if active else 4
        draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=width)
    seq = state["sequence"]
    start_x = (CANVAS - len(seq) * 48) // 2
    y = 286
    for i, color in enumerate(seq):
        x = start_x + i * 48 + 24
        active = i == state["play_index"]
        draw.ellipse((x - 16, y - 16, x + 16, y + 16), fill=COLORS[color], outline=(255, 245, 170) if active else (230, 235, 245), width=5 if active else 2)
    img.save(path)


def build_state(rng: random.Random, kind: str) -> Dict:
    palette = list(COLORS)
    seq = [rng.choice(palette) for _ in range(rng.randint(4, 6))]
    play_index = rng.randrange(len(seq))
    return {"kind": kind, "sequence": seq, "play_index": play_index, "highlight": seq[play_index]}


def solve(state: Dict) -> str:
    return state["highlight"]


def record(idx: int, seed: int, state: Dict, answer: str, media: str) -> Dict:
    if state["kind"] == "current_highlight":
        q = "<image> This is a Simon board with four colored buttons. The button with the bright border is currently highlighted. What color is highlighted? Answer with one color name only."
        diff, score = "easy", 0.25
    else:
        q = "<image> This Simon board shows the played sequence as small dots across the center. The dot with the bright border is the current step, and the matching large button is highlighted. What color is the current step? Answer with one color name only."
        diff, score = "medium", 0.4
    choices = list(COLORS)
    return {"id": f"r_simon_v1-{seed}-{idx:05d}", "media": [media], "messages": [{"role": "user", "question": q, "answer": answer, "options": {}, "choices": choices, "hint": ""}], "metadata": {"classification": {"domain": "games", "task": "simon_sequence_tracking", "reasoning_type": "simulation", "visual_type": "grid_board", "rule_delivery_mode": "explicit_text_prompt"}, "dataset": {"slug": "simon_v1", "version": VERSION}, "provenance": {"source": "https://inventwithpython.com/blog/i-need-practice-programming-49-ideas-for-game-clones-to-code.html#simon", "method": "deterministic_rule_simulation", "seed": seed, "index": idx, "seed_description": "Four-button Simon board with color sequence and active play index.", "generator": f"{SCRIPT_NAME}@{VERSION}", "rule_source": RULE_SOURCE}, "gt": {"answer": answer, "answer_text": answer, "answer_type": "string", "choices": choices, "validator": {"kind": "exact_match", "solution": answer}}, "instance": {"difficulty": diff, "complexity_score": score, "reasoning_depth": 1, "visual_load": len(state["sequence"]) / 8, "tags": ["simon", "sequence", "highlight"], "raw_state": state}}}


def write_jsonl(items: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def generate(out_dir: Path, count: int, seed: int) -> List[Dict]:
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed); records = []
    for idx in range(count):
        s = rng.randint(10_000_000, 999_999_999)
        state = build_state(random.Random(s), ["current_highlight", "sequence_current"][idx % 2])
        ans = solve(state); img = f"images/{idx:05d}.png"; render(state, out_dir / img)
        records.append(record(idx, s, state, ans, img))
    write_jsonl(records, out_dir / "vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id": "simon_v1.rule", "rule": "The highlighted button is the current color in the Simon sequence."}], out_dir / "rules.jsonl")
    quality = [{"id": r["id"], "keep": solve(r["metadata"]["instance"]["raw_state"]) == r["metadata"]["gt"]["answer"], "reason": "sequence verifier", "answer": r["metadata"]["gt"]["answer"]} for r in records]
    (out_dir / "quality_report.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"dataset": "simon_v1", "version": VERSION, "generator": SCRIPT_NAME, "count": len(records), "seed": seed, "build_complexity": "low", "reasoning_max": "medium", "rule_source": RULE_SOURCE, "format": "format_docs/VQA_DATA_FORMAT.md", "classification": "format_docs/classification.md", "reproduce_command": f"python3 generator/{SCRIPT_NAME} --count {len(records)} --seed {seed} --out-dir {out_dir}", "outputs": {"records": "vis_scaling_simple_mm.jsonl", "rules": "rules.jsonl", "quality_report": "quality_report.json", "images": "images/"}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(q["keep"] for q in quality): raise RuntimeError("quality verification failed")
    return records


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", default="generated/simon_v1"); p.add_argument("--count", type=int, default=2); p.add_argument("--seed", type=int, default=20260521); a = p.parse_args()
    print(f"Wrote {len(generate(Path(a.out_dir), a.count, a.seed))} Simon VQA records to {a.out_dir}")


if __name__ == "__main__": main()

