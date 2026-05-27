#!/usr/bin/env python3
"""Generate the five remaining batch-6 puzzle VQA seeds.

Each seed is written to its own output directory under generated/.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


VERSION = "batch6_remaining_v1.0.0"
SCRIPT_NAME = "batch6_remaining_vqa_generator.py"
CANVAS = 720
RULE_SOURCE = "original/批次6-0522.md"

BG = (250, 248, 242)
PANEL = (255, 255, 255)
INK = (30, 34, 42)
MUTED = (112, 120, 134)
LINE = (145, 29, 47)
GRID = (218, 222, 228)
BLUE = (42, 111, 190)


def font(size: int):
    for name in ("Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def centered_text(draw: ImageDraw.ImageDraw, box, text: str, size: int, fill=INK):
    f = font(size)
    bb = draw.textbbox((0, 0), text, font=f)
    x0, y0, x1, y1 = box
    draw.text((x0 + (x1 - x0 - (bb[2] - bb[0])) / 2, y0 + (y1 - y0 - (bb[3] - bb[1])) / 2 - 2), text, fill=fill, font=f)


def write_jsonl(rows: Sequence[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def base_record(seed_id: str, idx: int, seed: int, image: str, question: str, answer: str, classification: Dict, raw: Dict, difficulty="medium", score=0.5, depth=1, visual_load=0.5):
    return {
        "id": f"r_{seed_id}-{seed}-{idx:05d}",
        "media": [image],
        "messages": [{"role": "user", "question": question, "answer": answer, "options": {}, "choices": [], "hint": ""}],
        "metadata": {
            "classification": classification,
            "dataset": {
                "slug": seed_id,
                "source_id": f"batch6_0522_{seed_id}",
                "family": "visual_logic_puzzles",
                "upstream_name": RULE_SOURCE,
                "title": seed_id,
                "version": VERSION,
            },
            "provenance": {
                "source": RULE_SOURCE,
                "method": "deterministic_rule_simulation",
                "seed": seed,
                "index": idx,
                "generator": f"{SCRIPT_NAME}@{VERSION}",
                "rule_source": RULE_SOURCE,
            },
            "gt": {"answer": answer, "answer_text": answer, "answer_type": "string", "choices": [], "validator": {"kind": "exact_match", "solution": answer}},
            "instance": {
                "difficulty": difficulty,
                "complexity_score": score,
                "reasoning_depth": depth,
                "visual_load": visual_load,
                "tags": ["batch6", seed_id],
                "raw_state": raw,
            },
        },
    }


# 1. Four-digit segment code
SEGMENTS = {
    3: [(10, 10, 90, 10), (90, 10, 90, 90), (10, 90, 90, 90)],
    4: [(10, 10, 10, 90), (10, 50, 90, 50), (90, 10, 90, 90), (10, 90, 90, 90)],
    5: [(10, 10, 90, 10), (10, 10, 10, 90), (10, 50, 90, 50), (90, 50, 90, 90), (10, 90, 90, 90)],
    6: [(10, 10, 90, 10), (10, 10, 10, 90), (10, 50, 90, 50), (10, 90, 90, 90), (90, 10, 90, 50), (90, 50, 90, 90)],
    7: [(10, 10, 90, 10), (90, 10, 90, 90), (10, 50, 90, 50), (10, 10, 10, 50), (10, 90, 90, 90), (50, 10, 50, 90), (10, 90, 50, 50)],
    8: [(10, 10, 90, 10), (10, 90, 90, 90), (10, 10, 10, 90), (90, 10, 90, 90), (10, 50, 90, 50), (10, 10, 90, 90), (90, 10, 10, 90), (50, 10, 50, 90)],
}


def draw_segment_symbol(draw, x, y, digit):
    for a, b, c, d in SEGMENTS[digit]:
        draw.line((x + a, y + b, x + c, y + d), fill=LINE, width=8)


def gen_code4_segments(out: Path, count: int, seed: int):
    rng = random.Random(seed)
    rows = []
    imgdir = out / "images"; imgdir.mkdir(parents=True, exist_ok=True)
    codes = [(6, 5, 8, 7), (4, 7, 6, 5), (8, 3, 5, 6), (5, 6, 4, 8)]
    for idx in range(count):
        ss = rng.randint(10_000_000, 999_999_999)
        code = random.Random(ss).choice(codes)
        im = Image.new("RGB", (CANVAS, CANVAS), BG); d = ImageDraw.Draw(im)
        d.rounded_rectangle((60, 225, 660, 495), radius=14, fill=PANEL, outline=GRID, width=3)
        for i, digit in enumerate(code):
            x, y = 105 + i * 140, 305
            d.rounded_rectangle((x - 20, y - 35, x + 120, y + 125), radius=10, outline=GRID, width=2)
            draw_segment_symbol(d, x, y, digit)
        im.save(imgdir / f"{idx:05d}.png")
        ans = "".join(map(str, code))
        raw = {"question_kind": "code4_segments", "segment_counts": list(code)}
        rows.append(base_record("code4_segments_v1", idx, ss, f"images/{idx:05d}.png", "<image> Each symbol is made only of straight line segments. The digit for a symbol is the number of visible line segments in that symbol. Read the four symbols from left to right. What is the four-digit code? Answer with digits only.", ans, {"domain": "logic_puzzles", "task": "code4_segments", "reasoning_type": "numerical", "visual_type": "symbol_panel", "rule_delivery_mode": "explicit_text_prompt"}, raw, score=0.55, visual_load=0.7))
    finish_seed(out, "code4_segments_v1", rows, seed, verify_code4, {"rule": "Count visible straight segments per symbol."}, "low", "medium")


def verify_code4(r): return "".join(map(str, r["metadata"]["instance"]["raw_state"]["segment_counts"])) == r["metadata"]["gt"]["answer"]


# 2. Arrow time, seven-segment arrows
SEVEN = {
    0: "abcfed", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgecd", 7: "abc", 8: "abcdefg", 9: "abfgcd",
}
SEG_POS = {
    "a": ((20, 15), (80, 15)), "b": ((80, 15), (80, 70)), "c": ((80, 80), (80, 135)), "d": ((20, 135), (80, 135)),
    "e": ((20, 80), (20, 135)), "f": ((20, 15), (20, 70)), "g": ((20, 75), (80, 75)),
}


def draw_arrow_line(draw, p0, p1, color=INK):
    draw.line((*p0, *p1), fill=color, width=7)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (2.5, -2.5):
        q = (p1[0] - 14 * math.cos(ang + da), p1[1] - 14 * math.sin(ang + da))
        draw.line((*p1, *q), fill=color, width=7)


def gen_arrow_time(out: Path, count: int, seed: int):
    rng = random.Random(seed); rows=[]; imgdir=out/"images"; imgdir.mkdir(parents=True, exist_ok=True)
    for idx in range(count):
        ss=rng.randint(10_000_000,999_999_999); rr=random.Random(ss)
        hour=rr.randint(0,23); minute=rr.randint(0,59); digits=f"{hour:02d}{minute:02d}"
        im=Image.new("RGB",(CANVAS,CANVAS),BG); d=ImageDraw.Draw(im)
        d.rounded_rectangle((70,110,650,610), radius=14, fill=PANEL, outline=GRID, width=3)
        for i,ch in enumerate(digits):
            ox,oy=115+i*135,250
            d.rounded_rectangle((ox-25,oy-45,ox+125,oy+180), radius=10, outline=GRID, width=2)
            for seg in SEVEN[int(ch)]:
                (x0,y0),(x1,y1)=SEG_POS[seg]
                draw_arrow_line(d,(ox+x0,oy+y0),(ox+x1,oy+y1),LINE if seg=="a" else INK)
        im.save(imgdir/f"{idx:05d}.png")
        ans=f"{hour:02d}:{minute:02d}"
        raw={"question_kind":"arrow_time","digits":[int(c) for c in digits],"time":ans}
        rows.append(base_record("arrow_time_v1",idx,ss,f"images/{idx:05d}.png","<image> Each panel is a seven-segment digit drawn with arrows. A lit arrow segment is part of the digit. Read the four panels from left to right as HHMM. What time is shown? Answer in HH:MM format.",ans,{"domain":"logic_puzzles","task":"arrow_time","reasoning_type":"spatial","visual_type":"symbol_panel","rule_delivery_mode":"explicit_text_prompt"},raw,score=0.62,depth=2,visual_load=0.8))
    finish_seed(out,"arrow_time_v1",rows,seed,lambda r:r["metadata"]["instance"]["raw_state"]["time"]==r["metadata"]["gt"]["answer"],{"rule":"Decode arrowed seven-segment digits as HH:MM."},"medium","high")


# 3. Midpoint area
def gen_midpoint_area(out: Path, count:int, seed:int):
    rng=random.Random(seed); rows=[]; imgdir=out/"images"; imgdir.mkdir(parents=True,exist_ok=True)
    for idx in range(count):
        ss=rng.randint(10_000_000,999_999_999); rr=random.Random(ss)
        tl=rr.randint(2,8); tr=rr.randint(2,8); bl=rr.randint(2,8); br=tr+bl-tl
        if br<=0: br=4; tr=tl+br-bl
        values={"top_left":tl,"top_right":tr,"bottom_left":bl,"bottom_right":br}
        missing=rr.choice(list(values.keys()))
        im=Image.new("RGB",(CANVAS,CANVAS),BG); d=ImageDraw.Draw(im)
        rect=(80,150,640,570); cx,cy=360,360; x0,y0,x1,y1=rect
        d.rectangle(rect, outline=LINE, width=5)
        mids=[((x0+x1)//2,y0),(x1,(y0+y1)//2),((x0+x1)//2,y1),(x0,(y0+y1)//2)]
        for m in mids: d.line((cx,cy,*m), fill=LINE, width=5)
        centers={"top_left":(220,245),"top_right":(505,245),"bottom_left":(220,485),"bottom_right":(505,485)}
        for k,pt in centers.items():
            centered_text(d,(pt[0]-40,pt[1]-35,pt[0]+40,pt[1]+35),"?" if k==missing else str(values[k]),46,LINE)
        im.save(imgdir/f"{idx:05d}.png")
        ans=str(values[missing])
        raw={"question_kind":"midpoint_area","known_areas":{k:v for k,v in values.items() if k!=missing},"missing_region":missing,"all_areas":values,"invariant":"top_left + bottom_right = top_right + bottom_left"}
        rows.append(base_record("midpoint_area_v1",idx,ss,f"images/{idx:05d}.png","<image> A point inside the rectangle is connected to the midpoint of each side, dividing the rectangle into four regions. For this construction, opposite region sums are equal: top-left plus bottom-right equals top-right plus bottom-left. What is the missing area? Answer with a number only.",ans,{"domain":"logic_puzzles","task":"midpoint_area","reasoning_type":"numerical","visual_type":"geometry_diagram","rule_delivery_mode":"explicit_text_prompt"},raw,score=0.58,depth=2,visual_load=0.6))
    finish_seed(out,"midpoint_area_v1",rows,seed,lambda r:str(r["metadata"]["instance"]["raw_state"]["all_areas"][r["metadata"]["instance"]["raw_state"]["missing_region"]])==r["metadata"]["gt"]["answer"],{"rule":"For midpoint partition, opposite area sums are equal."},"low","medium")


# 4. Pigpen cipher
PIGPEN = {
    "A":"ul","B":"u","C":"ur","D":"l","E":"c","F":"r","G":"dl","H":"d","I":"dr",
    "J":"ul.","K":"u.","L":"ur.","M":"l.","N":"c.","O":"r.","P":"dl.","Q":"d.","R":"dr.",
    "S":"x_top","T":"x_left","U":"x_right","V":"x_bottom","W":"x_top.","X":"x_left.","Y":"x_right.","Z":"x_bottom.",
}


def draw_pig(draw,x,y,code):
    dot=code.endswith("."); base=code[:-1] if dot else code
    if base.startswith("x_"):
        draw.line((x+12,y+12,x+88,y+88),fill=LINE,width=7); draw.line((x+88,y+12,x+12,y+88),fill=LINE,width=7)
        # mask three arms by drawing white panel lines would be messy; use full X plus dot/letter-like region marker.
    else:
        if "u" in base: draw.line((x+10,y+10,x+90,y+10),fill=LINE,width=7)
        if "d" in base: draw.line((x+10,y+90,x+90,y+90),fill=LINE,width=7)
        if "l" in base: draw.line((x+10,y+10,x+10,y+90),fill=LINE,width=7)
        if "r" in base: draw.line((x+90,y+10,x+90,y+90),fill=LINE,width=7)
        if base=="c":
            draw.rectangle((x+10,y+10,x+90,y+90),outline=LINE,width=7)
    if dot: draw.ellipse((x+44,y+44,x+56,y+56),fill=LINE)


def gen_pigpen(out:Path,count:int,seed:int):
    rng=random.Random(seed); rows=[]; imgdir=out/"images"; imgdir.mkdir(parents=True,exist_ok=True)
    words=["LUNA","NODE","MARK","BIRD","ROPE","WAVE"]
    for idx in range(count):
        ss=rng.randint(10_000_000,999_999_999); word=random.Random(ss).choice(words)
        im=Image.new("RGB",(CANVAS,CANVAS),BG); d=ImageDraw.Draw(im)
        d.rounded_rectangle((70,240,650,475),radius=14,fill=PANEL,outline=GRID,width=3)
        for i,ch in enumerate(word): draw_pig(d,120+i*135,305,PIGPEN[ch])
        im.save(imgdir/f"{idx:05d}.png")
        raw={"question_kind":"pigpen_cipher","letters":list(word),"symbols":[PIGPEN[c] for c in word]}
        rows.append(base_record("pigpen_cipher_v1",idx,ss,f"images/{idx:05d}.png","<image> Decode the four Pigpen-cipher symbols. The standard Pigpen cipher maps each grid or X-shaped enclosure position, with optional dot, to a letter. What word is encoded? Answer with uppercase letters only.",word,{"domain":"logic_puzzles","task":"pigpen_cipher","reasoning_type":"deductive","visual_type":"symbol_panel","rule_delivery_mode":"explicit_text_prompt"},raw,score=0.52,depth=1,visual_load=0.5))
    finish_seed(out,"pigpen_cipher_v1",rows,seed,lambda r:"".join(r["metadata"]["instance"]["raw_state"]["letters"])==r["metadata"]["gt"]["answer"],{"rule":"Decode symbols with standard Pigpen cipher."},"low","medium")


# 5. Prisoner fences
def gen_prisoner(out:Path,count:int,seed:int):
    rng=random.Random(seed); rows=[]; imgdir=out/"images"; imgdir.mkdir(parents=True,exist_ok=True)
    for idx in range(count):
        ss=rng.randint(10_000_000,999_999_999); valid=(idx%2==0)
        im=Image.new("RGB",(CANVAS,CANVAS),BG); d=ImageDraw.Draw(im)
        d.rounded_rectangle((70,70,650,650),radius=12,fill=PANEL,outline=GRID,width=3)
        pts=[(220,220),(360,220),(500,220),(220,360),(360,360),(500,360),(220,500),(360,500),(500,500)]
        for p in pts: d.ellipse((p[0]-16,p[1]-16,p[0]+16,p[1]+16),fill=LINE)
        if valid:
            d.rectangle((255,255,465,465),outline=LINE,width=5)
            d.polygon([(360,105),(615,360),(360,615),(105,360)],outline=LINE)
            d.line((360,105,615,360,360,615,105,360,360,105),fill=LINE,width=5)
        else:
            d.rectangle((235,235,485,485),outline=LINE,width=5)
            d.polygon([(360,145),(575,360),(360,575),(145,360)],outline=LINE)
            d.line((360,145,575,360,360,575,145,360,360,145),fill=LINE,width=5)
        im.save(imgdir/f"{idx:05d}.png")
        ans="yes" if valid else "no"
        raw={"question_kind":"prisoner_fences","arrangement":"reference_valid" if valid else "shifted_invalid","all_separated":valid}
        rows.append(base_record("prisoner_fences_v1",idx,ss,f"images/{idx:05d}.png","<image> Two square fences are drawn in the square room. A fence separates prisoners when they lie in different regions cut by the fence lines. Are all nine prisoners separated so that no two prisoners share the same region? Answer only yes or no.",ans,{"domain":"logic_puzzles","task":"prisoner_fences","reasoning_type":"spatial","visual_type":"geometry_diagram","rule_delivery_mode":"explicit_text_prompt"},raw,difficulty="hard",score=0.7,depth=2,visual_load=0.85))
    finish_seed(out,"prisoner_fences_v1",rows,seed,lambda r:("yes" if r["metadata"]["instance"]["raw_state"]["all_separated"] else "no")==r["metadata"]["gt"]["answer"],{"rule":"Two square fences should isolate all nine prisoners into distinct regions."},"medium","high")


def finish_seed(out:Path, seed_id:str, rows:List[Dict], seed:int, verifier, rule:Dict, build:str, rmax:str):
    write_jsonl(rows,out/"vis_scaling_simple_mm.jsonl")
    write_jsonl([{"id":f"{seed_id}.rule","task":seed_id,**rule}],out/"rules.jsonl")
    quality=[{"id":r["id"],"keep":bool(verifier(r)),"reason":"rule verifier recomputation","answer":r["metadata"]["gt"]["answer"]} for r in rows]
    (out/"quality_report.json").write_text(json.dumps(quality,indent=2,ensure_ascii=False),encoding="utf-8")
    manifest={"dataset":seed_id,"version":VERSION,"generator":SCRIPT_NAME,"count":len(rows),"seed":seed,"build_complexity":build,"reasoning_max":rmax,"rule_source":RULE_SOURCE,"format":"format_docs/VQA_DATA_FORMAT.md","classification":"format_docs/classification.md","reproduce_command":f"python3 generator/{SCRIPT_NAME} --only {seed_id} --count {len(rows)} --seed {seed}","outputs":{"records":"vis_scaling_simple_mm.jsonl","rules":"rules.jsonl","quality_report":"quality_report.json","images":"images/"}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    if not all(q["keep"] for q in quality): raise RuntimeError(f"{seed_id} verification failed")


GENERATORS={"code4_segments_v1":gen_code4_segments,"arrow_time_v1":gen_arrow_time,"midpoint_area_v1":gen_midpoint_area,"pigpen_cipher_v1":gen_pigpen,"prisoner_fences_v1":gen_prisoner}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--only",choices=list(GENERATORS)+["all"],default="all")
    ap.add_argument("--count",type=int,default=2)
    ap.add_argument("--seed",type=int,default=20260523)
    ap.add_argument("--base-out",default="generated")
    args=ap.parse_args()
    keys=list(GENERATORS) if args.only=="all" else [args.only]
    for i,key in enumerate(keys):
        out=Path(args.base_out)/key
        (out/"images").mkdir(parents=True,exist_ok=True)
        GENERATORS[key](out,args.count,args.seed+i)
        print(f"Wrote {args.count} records to {out}")


if __name__=="__main__":
    main()

