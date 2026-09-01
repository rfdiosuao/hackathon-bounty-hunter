#!/usr/bin/env python3
"""
watcha.cn 观猹活动平台抓取模块
抓取 watcha 上的黑客松/赛事活动，提取报名链接和截止日期。
API: https://watcha.cn/api/v2/activities/v2?limit=100 (支持 skip/limit 翻页)

字段:
- id, title, slug, cover_url, short_description
- start_at, end_at (ISO 时间)
- location_type: online/offline, location, online_url
- registration_url, registration_mode
- description: 富文本(含奖金信息)
- redirect_url
"""
import json
import re
import sys
import hashlib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

CST = timezone(timedelta(hours=8))
WORK_DIR = Path(__file__).parent

API_BASE = "https://watcha.cn/api/v2/activities/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://watcha.cn/activities",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 赛事关键词：命中才保留
EVENT_KEYWORDS = [
    "黑客松", "Hackathon", "hackathon", "大赛", "挑战赛",
    "竞赛", "创作", "比赛", "创作挑战",
]

# 排除词：纯论坛/分享/大会/峰会/沙龙
EXCLUDE_KEYWORDS = [
    "大会", "峰会", "沙龙", "论坛", "分享会", "交流会",
    "Workshop", "workshop", "工作坊", "DemoDay", "路演",
    "发布会", "创作者大会", "猹话会", "派对", "参观",
]


def make_id(name: str, deadline: str) -> str:
    raw = f"{name.strip().lower()}|{deadline.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def extract_description_text(desc) -> str:
    """把富文本 description 提取为纯文本"""
    if not desc:
        return ""
    if isinstance(desc, str):
        return desc
    texts = []
    content = desc.get("content", []) if isinstance(desc, dict) else []
    for block in content:
        if block.get("type") == "paragraph":
            for node in block.get("content", []):
                if node.get("type") == "text":
                    texts.append(node.get("text", ""))
                elif node.get("type") == "hardBreak":
                    texts.append("\n")
            texts.append("\n")
        elif block.get("type") == "bulletList" or block.get("type") == "orderedList":
            for item in block.get("content", []):
                for para in item.get("content", []):
                    for node in para.get("content", []):
                        if node.get("type") == "text":
                            texts.append(node.get("text", ""))
                    texts.append("\n")
    return "".join(texts)


def extract_prize(text: str) -> str:
    """从描述文本提取奖金信息"""
    if not text:
        return ""
    prize = ""
    patterns = [
        r"(?:奖金|奖池|现金奖|大奖|奖励)[:：]?\s*[^。\n]{0,40}",
        r"(?:¥|￥|$|\$)?\s*\d[\d,，.]*\s*(?:万|元|美元|美金|k|K)\s*(?:奖池|奖金|大奖)?[^。\n]{0,20}",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            prize = m.group(0).strip()
            break
    if not prize:
        m = re.search(r"[^。\n]{0,15}(?:\d[\d,，.]*万|\d[\d,，.]*元|\$[\d,]+)\s*(?:奖池|奖金|现金|大奖)?[^。\n]{0,15}", text)
        if m:
            prize = m.group(0).strip()
    return prize[:80]


def extract_deadline(item: dict, desc_text: str) -> str:
    """提取截止日期"""
    end_at = item.get("end_at")
    if end_at:
        try:
            dt = datetime.fromisoformat(end_at)
            return dt.strftime("%Y-%m-%d")
        except:
            return end_at[:10]
    m = re.search(r"(?:截止|报名截止|截至|结束)[^\n]{0,20}(\d{4}\s*年)?\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", desc_text)
    if m:
        return f"{m.group(2)}月{m.group(3)}日"
    m = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", desc_text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def fetch_watcha() -> list:
    """抓取 watcha 全部赛事活动"""
    all_items = []
    try:
        r = requests.get(API_BASE, params={"limit": 100}, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("items", [])
        all_items.extend(items)
        total = data.get("data", {}).get("total", len(items))
        print(f"  watcha 首页: {len(items)} 条，总计约 {total}")
        time.sleep(1)
        skip = len(items)
        while skip < total:
            r = requests.get(API_BASE, params={"skip": skip, "limit": 20}, headers=HEADERS, timeout=20)
            r.raise_for_status()
            d = r.json()
            batch = d.get("data", {}).get("items", [])
            if not batch:
                break
            all_items.extend(batch)
            skip += len(batch)
            time.sleep(0.8)
            if len(all_items) > 500:
                break
    except Exception as e:
        print(f"  [WARN] watcha 抓取异常: {e}", file=sys.stderr)

    seen = set()
    unique = []
    for it in all_items:
        if it["id"] not in seen:
            seen.add(it["id"])
            unique.append(it)

    events = []
    now = datetime.now(CST)
    for item in unique:
        title = item.get("title", "").strip()
        if not title:
            continue
        if not any(k.lower() in title.lower() for k in EVENT_KEYWORDS):
            continue
        if any(k.lower() in title.lower() for k in EXCLUDE_KEYWORDS):
            continue

        desc_text = extract_description_text(item.get("description"))
        deadline = extract_deadline(item, desc_text)
        prize = extract_prize(desc_text)

        loc_type = item.get("location_type", "")
        location = ""
        loc = item.get("location")
        if isinstance(loc, dict):
            location = loc.get("name") or loc.get("city") or ""
        if not location and isinstance(loc, str):
            location = loc
        if loc_type == "online":
            location = "线上" + (f"·{location}" if location else "")

        apply_url = item.get("registration_url") or item.get("online_url") or item.get("redirect_url") or ""
        if not apply_url:
            m = re.search(r"https?://[^\s)\"']+", desc_text)
            if m:
                apply_url = m.group(0)

        start_at = item.get("start_at", "")[:10]

        try:
            if deadline and re.match(r"^20\d\d-\d\d-\d\d$", deadline):
                dd = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=CST)
                if dd < now - timedelta(days=7) or dd > now + timedelta(days=120):
                    continue
        except Exception:
            pass

        events.append({
            "id": make_id(title, deadline),
            "watcha_id": item["id"],
            "name": title,
            "host": "",
            "location": location,
            "format": "线上" if loc_type == "online" else "线下",
            "prize": prize,
            "deadline": deadline or start_at,
            "start_at": start_at,
            "apply_url": apply_url,
            "status": "观猹watcha",
            "source": "观猹watcha",
            "found_date": now.strftime("%Y-%m-%d"),
        })

    return events


def main():
    print("抓取观猹 watcha 赛事...")
    events = fetch_watcha()
    print(f"  watcha 解析出 {len(events)} 个赛事")
    for e in events:
        print(f"    - {e['name'][:40]} | {e['location'][:15]} | 截止:{e['deadline'][:12]} | {e['apply_url'][:45]}")
    out = WORK_DIR / "watcha_events.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"  已保存到 {out}")
    return events


if __name__ == "__main__":
    main()
