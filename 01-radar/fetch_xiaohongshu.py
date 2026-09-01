#!/usr/bin/env python3
"""
黑客松雷达 - 小红书博主信息抓取模块
抓取指定小红书博主的笔记，从笔记正文(og:description)中提取赛事信息。

支持两种输入：
1. 笔记链接（xhslink.cn 短链 / xiaohongshu.com 详情页）
2. 博主主页（需先获取主页的笔记列表）

注意：小红书有反爬，单个IP频繁抓取可能被限流。建议控制抓取频率。
"""

import json
import re
import hashlib
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WORK_DIR = Path(__file__).parent
CST = timezone(timedelta(hours=8))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def make_id(name: str, deadline: str) -> str:
    raw = f"{name.strip().lower()}|{deadline.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def resolve_shortlink(url: str) -> str:
    """解析 xhslink.cn 短链为真实链接"""
    try:
        resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        return resp.url
    except Exception as e:
        print(f"  [WARN] 短链解析失败 {url}: {e}", file=sys.stderr)
        return url


def extract_note_id(url: str) -> str:
    """从 URL 中提取笔记 ID"""
    m = re.search(r"/(?:discovery/item|explore|item|note)/?([0-9a-f]+)", url)
    if m:
        return m.group(1)
    return ""


def fetch_note(url: str) -> dict:
    """抓取单篇笔记，返回标题和正文"""
    real_url = resolve_shortlink(url)
    note_id = extract_note_id(real_url)
    try:
        resp = requests.get(real_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.title.string.strip() if soup.title else ""
        desc = ""
        for meta in soup.find_all("meta"):
            prop = meta.get("property") or meta.get("name")
            if prop == "og:description":
                desc = meta.get("content", "")
                break

        text = soup.get_text(" ", strip=True)

        user_id = ""
        m = re.search(r'"userId":"([0-9a-f]+)"', resp.text)
        if m:
            user_id = m.group(1)

        return {
            "note_id": note_id,
            "url": real_url,
            "title": title,
            "description": desc,
            "author_user_id": user_id,
            "fetched_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"  [WARN] 笔记抓取失败 {url}: {e}", file=sys.stderr)
        return None


def parse_events_from_note(note: dict) -> list:
    """
    从笔记正文中解析赛事信息，支持两种格式：
    A. 编号列表格式（1️⃣ xxx 📍地点 📅日期）
    B. 段落式周报格式（赛事名 描述 奖金:xx 截止日期:xx）
    """
    if not note or not note.get("description"):
        return []

    text = note["description"]
    events = []

    segments = re.split(r"\d+[️⃣.]", text)
    segments = [s.strip() for s in segments if s.strip()]

    emoji_seg_count = len([s for s in segments if "📍" in s or "📅" in s])
    if emoji_seg_count >= 2:
        for seg in segments[1:]:
            lines = [l.strip() for l in seg.split("\n") if l.strip()]
            if not lines:
                continue
            name = lines[0].strip()
            name = re.sub(r"^【推荐】\s*", "", name)

            location = ""
            m = re.search(r"📍\s*([^\n]+)", seg)
            if m:
                location = m.group(1).strip()
            else:
                m = re.search(r"地点[:：]\s*([^\n]+)", seg)
                if m:
                    location = m.group(1).strip()

            date_text = ""
            m = re.search(r"📅\s*([^\n]+)", seg)
            if m:
                date_text = m.group(1).strip()
            else:
                m = re.search(r"日期[:：]\s*([^\n]+)", seg)
                if m:
                    date_text = m.group(1).strip()

            prize = ""
            m = re.search(r"奖金[:：]\s*([^\n]+)", seg)
            if m:
                prize = m.group(1).strip()

            deadline = ""
            m = re.search(r"截止日期[:：]\s*([^\n]+)", seg)
            if m:
                deadline = m.group(1).strip()
            elif date_text:
                deadline = date_text

            apply_url = ""
            m = re.search(r"(https?://[^\s\)\]，,;]+)", seg)
            if m:
                apply_url = m.group(1).strip()

            if name and len(name) > 3:
                events.append({
                    "id": make_id(name, deadline),
                    "name": name,
                    "host": "",
                    "location": location,
                    "format": "",
                    "prize": prize,
                    "deadline": deadline,
                    "apply_url": apply_url,
                    "status": "小红书笔记",
                    "source": note.get("title", "小红书"),
                    "found_date": datetime.now(CST).strftime("%Y-%m-%d"),
                })
    else:
        blocks = re.split(r"\t+|\n+", text)
        blocks = [b.strip() for b in blocks if b.strip()]

        event_blocks = []
        current = ""
        raw_blocks = re.split(r"\s{2,}|\t+", text)
        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            if any(kw in block[:15] for kw in ["考虑到", "找不到队友", "我的黑客松", "避坑", "找队友", "加入黑客松", "为了", "我们"]):
                continue
            current += block + " "
            if "截止日期" in block or "截止：" in block:
                event_blocks.append(current.strip())
                current = ""

        for eb in event_blocks:
            desc_kws = r"看点|把AI|聚焦|面向|围绕|让Agent|聚焦Agent|把多智能体|联合|携手|邀请|欢迎|面向全国"
            name = eb
            m = re.search(desc_kws, eb)
            if m:
                name = eb[:m.start()].strip()
            else:
                name = re.split(r"[，,。;；]", eb)[0].strip()
            name = re.sub(r"^【推荐】\s*", "", name)
            name = re.sub(r"[，,。;；:：].*$", "", name).strip()
            name = re.sub(r"(?:第三|第\d+|NVIDIA).*$", "", name) if "NVIDIA" in name else name
            name = name.strip()
            if len(name) > 40:
                name = name[:40]

            location = ""
            m = re.search(r"(?:地点|📍)[:：]?\s*([^\s，,。]+)", eb)
            if m:
                location = m.group(1).strip()

            prize = ""
            m = re.search(r"奖金[:：]\s*([^；;\n]+)", eb)
            if m:
                prize = m.group(1).strip()

            deadline = ""
            m = re.search(r"截止日期[:：]\s*([^；;\n]+)", eb)
            if m:
                deadline = m.group(1).strip()
            elif m := re.search(r"截止[:：]\s*([^；;\n]+)", eb):
                deadline = m.group(1).strip()

            apply_url = ""
            m = re.search(r"(https?://[^\s\)\]，,;]+)", eb)
            if m:
                apply_url = m.group(1).strip()

            if name and len(name) > 3 and "避坑" not in name and "小贴士" not in name:
                events.append({
                    "id": make_id(name, deadline),
                    "name": name,
                    "host": "",
                    "location": location,
                    "format": "",
                    "prize": prize,
                    "deadline": deadline,
                    "apply_url": apply_url,
                    "status": "小红书笔记",
                    "source": note.get("title", "小红书"),
                    "found_date": datetime.now(CST).strftime("%Y-%m-%d"),
                })

    return events


XHS_SOURCES = [
    {
        "name": "杭州AI工坊",
        "type": "note",
        "url": "https://xhslink.cn/o/6AWI7fUjemt",
        "user_id": "5cc5d87400000000120278a2",
    },
    {
        "name": "黑客松周报",
        "type": "note",
        "url": "https://xhslink.cn/o/8ItMKYhiWzF",
        "user_id": "",
    },
    {
        "name": "数字小蕾的AI实验室",
        "type": "note",
        "url": "https://xhslink.cn/o/8EOu1LNI9Cv",
        "user_id": "",
    },
]


def fetch_all_xhs() -> list:
    """抓取所有配置的小红书源，返回赛事列表"""
    all_events = []
    for src in XHS_SOURCES:
        print(f"  抓取小红书源: {src['name']}")
        note = fetch_note(src["url"])
        if note:
            events = parse_events_from_note(note)
            print(f"    笔记《{note['title'][:30]}》解析出 {len(events)} 个赛事")
            all_events.extend(events)
        time.sleep(2)
    return all_events


if __name__ == "__main__":
    events = fetch_all_xhs()
    print(f"\n共解析出 {len(events)} 个赛事:")
    for e in events:
        print(f"  - {e['name'][:40]} | {e['location'][:20]} | 截止:{e['deadline'][:20]}")
    out = WORK_DIR / "xhs_events.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {out}")
