#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


KEYWORDS = ["推理游戏", "动脑", "游戏", "益脑", "事业单位"]
XHS = "/Users/yezixiao/.local/bin/xhs"
OUT_DIR = Path(__file__).resolve().parent


def run_search(keyword, page=1):
    cmd = [XHS, "search", keyword, "--page", str(page), "--json"]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        return {"keyword": keyword, "page": page, "ok": False, "error": proc.stderr.strip() or proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"keyword": keyword, "page": page, "ok": False, "error": f"Invalid JSON: {exc}"}


def pick_image_urls(note_card):
    urls = []
    for image in note_card.get("image_list") or []:
        chosen = None
        for info in image.get("info_list") or []:
            if info.get("image_scene") == "WB_DFT" and info.get("url"):
                chosen = info["url"]
                break
        if not chosen:
            for info in image.get("info_list") or []:
                if info.get("url"):
                    chosen = info["url"]
                    break
        if chosen:
            urls.append(chosen)
    cover = note_card.get("cover") or {}
    if cover.get("url_default") and cover["url_default"] not in urls:
        urls.insert(0, cover["url_default"])
    return urls


def publish_time(note_card):
    for item in note_card.get("corner_tag_info") or []:
        if item.get("type") == "publish_time":
            return item.get("text", "")
    return ""


def normalize_item(item, keyword, rank):
    card = item.get("note_card") or {}
    user = card.get("user") or {}
    interact = card.get("interact_info") or {}
    note_id = item.get("id", "")
    title = card.get("display_title", "")
    image_urls = pick_image_urls(card)
    return {
        "source": "xiaohongshu",
        "query_keyword": keyword,
        "rank": rank,
        "note_id": note_id,
        "note_url": f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
        "title": title,
        "caption_excerpt": title[:120],
        "author_name": user.get("nickname") or user.get("nick_name") or "",
        "author_id": user.get("user_id", ""),
        "publish_time": publish_time(card),
        "liked_count": interact.get("liked_count", ""),
        "collected_count": interact.get("collected_count", ""),
        "comment_count": interact.get("comment_count", ""),
        "shared_count": interact.get("shared_count", ""),
        "note_type": card.get("type", ""),
        "image_count": len(image_urls),
        "image_urls": image_urls,
        "image_downloaded": False,
    }


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path, rows):
    fieldnames = [
        "source",
        "query_keyword",
        "rank",
        "note_id",
        "note_url",
        "title",
        "caption_excerpt",
        "author_name",
        "author_id",
        "publish_time",
        "liked_count",
        "collected_count",
        "comment_count",
        "shared_count",
        "note_type",
        "image_count",
        "image_urls",
        "image_downloaded",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["image_urls"] = " ".join(row["image_urls"])
            writer.writerow(out)


def write_readme(path, rows, errors):
    by_keyword = {}
    for row in rows:
        by_keyword[row["query_keyword"]] = by_keyword.get(row["query_keyword"], 0) + 1
    lines = [
        "# dataset_find",
        "",
        "Xiaohongshu search-result dataset collected with Agent Reach/xhs-cli.",
        "",
        f"- collected_at_utc: {datetime.now(timezone.utc).isoformat()}",
        f"- keywords: {', '.join(KEYWORDS)}",
        f"- unique_posts: {len(rows)}",
        "- files: posts.jsonl, posts.csv, raw_search/*.json",
        "- copyright note: this dataset stores public metadata, short title/excerpt fields, source links, and image URLs. It does not download original images or copy full post text.",
        "",
        "## Counts",
        "",
    ]
    for keyword in KEYWORDS:
        lines.append(f"- {keyword}: {by_keyword.get(keyword, 0)}")
    if errors:
        lines.extend(["", "## Errors", ""])
        for err in errors:
            lines.append(f"- {err}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    raw_dir = OUT_DIR / "raw_search"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    errors = []

    for keyword in KEYWORDS:
        data = run_search(keyword, page=1)
        (raw_dir / f"{keyword}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if not data.get("ok"):
            errors.append(f"{keyword}: {data.get('error', 'unknown error')}")
            continue
        items = ((data.get("data") or {}).get("items") or [])
        rank = 0
        for item in items:
            note_id = item.get("id")
            if not note_id or note_id in seen:
                continue
            seen.add(note_id)
            rank += 1
            rows.append(normalize_item(item, keyword, rank))

    write_jsonl(OUT_DIR / "posts.jsonl", rows)
    write_csv(OUT_DIR / "posts.csv", rows)
    write_readme(OUT_DIR / "README.md", rows, errors)
    print(json.dumps({"ok": True, "unique_posts": len(rows), "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
