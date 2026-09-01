#!/usr/bin/env python3
"""
黑客松雷达 - 结构化来源抓取脚本
来源：HackHQ (GitHub 结构化表格，jsdelivr CDN)
输出：latest_all.json (全量)、latest_new.json (新增)
"""

import json
import hashlib
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

WORK_DIR = Path(__file__).parent
PUSHED_FILE = WORK_DIR / "pushed.json"
OUTPUT_FILE = WORK_DIR / "latest_new.json"
RAW_FILE = WORK_DIR / "latest_all.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

CST = timezone(timedelta(hours=8))


def make_id(name: str, deadline: str) -> str:
    raw = f"{name.strip().lower()}|{deadline.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def clean_text(text: str) -> str:
    text = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>.*?</a>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"[🔥]\s*", "", text)
    return text.strip()


def extract_url(text: str) -> str:
    m = re.search(r'href="([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(r"https?://[^\s\)\"']+", text)
    if m:
        return m.group(0)
    return ""


def load_pushed() -> dict:
    if PUSHED_FILE.exists():
        with open(PUSHED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def fetch_hackhq() -> list:
    """从 HackHQ 抓取结构化黑客松列表"""
    urls = [
        "https://cdn.jsdelivr.net/gh/Jose-Gael-Cruz-Lopez/hackhq@main/README.md",
        "https://raw.githubusercontent.com/Jose-Gael-Cruz-Lopez/hackhq/main/README.md",
    ]
    text = None
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            text = resp.text
            print(f"  HackHQ 数据源: {url}")
            break
        except Exception as e:
            print(f"  HackHQ 尝试失败 ({url}): {e}", file=sys.stderr)

    if not text:
        return []

    competitions = []
    start = text.find("<!-- HACKATHONS_TABLE_START -->")
    if start == -1:
        start = text.find("| Status | Host |")
    end = text.find("<!-- HACKATHONS_TABLE_END -->", start)
    if end == -1:
        next_section = text.find("\n## ", start + 100)
        end = next_section if next_section != -1 else start + 50000
    table_text = text[start:end]

    lines = table_text.split("\n")
    headers = []
    past_separator = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if past_separator:
                break
            continue
        if re.match(r"^\|[\s\-:|]+\|$", stripped):
            past_separator = True
            continue
        if not headers and not past_separator:
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            continue
        if headers and past_separator:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= len(headers):
                row = dict(zip(headers, cells))
                name = clean_text(row.get("Hackathon", ""))
                if name and name.lower() != "hackathon" and len(name) > 3:
                    deadline = clean_text(row.get("Deadline", ""))
                    if deadline in ("—", "-", ""):
                        deadline = ""
                    apply_url = extract_url(row.get("Application", ""))
                    competitions.append({
                        "id": make_id(name, deadline),
                        "name": name,
                        "host": clean_text(row.get("Host", "")),
                        "location": clean_text(row.get("Location", "")),
                        "format": clean_text(row.get("Format", "")),
                        "prize": clean_text(row.get("Prize", "")),
                        "deadline": deadline,
                        "apply_url": apply_url,
                        "status": clean_text(row.get("Status", "")),
                        "source": "HackHQ",
                        "found_date": datetime.now(CST).strftime("%Y-%m-%d"),
                    })
    return competitions


def deduplicate(competitions: list) -> list:
    seen = {}
    for c in competitions:
        cid = c["id"]
        if cid not in seen:
            seen[cid] = c
        else:
            existing = seen[cid]
            for k, v in c.items():
                if not existing.get(k) and v:
                    existing[k] = v
    return list(seen.values())


def main():
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 开始抓取黑客松信息...")

    all_competitions = fetch_hackhq()
    print(f"  HackHQ 抓取: {len(all_competitions)} 条")

    all_competitions = deduplicate(all_competitions)
    print(f"  去重后: {len(all_competitions)} 条")

    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(all_competitions, f, ensure_ascii=False, indent=2)

    pushed = load_pushed()
    new_competitions = [c for c in all_competitions if c["id"] not in pushed]
    print(f"  新增(未推送): {len(new_competitions)} 条")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_competitions, f, ensure_ascii=False, indent=2)

    for i, c in enumerate(new_competitions[:5]):
        print(f"  [{i+1}] {c['name'][:50]} | 截止:{c['deadline']} | {c['source']}")

    summary = {"total": len(all_competitions), "new_count": len(new_competitions)}
    print("===SUMMARY===")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
