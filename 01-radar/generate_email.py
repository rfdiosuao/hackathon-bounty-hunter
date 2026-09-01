#!/usr/bin/env python3
"""
黑客松雷达 - 邮件内容生成器
读取 latest_new.json，生成 HTML 邮件正文
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORK_DIR = Path(__file__).parent
NEW_FILE = WORK_DIR / "latest_new.json"
CST = timezone(timedelta(hours=8))


def generate_html(competitions: list) -> str:
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")

    rows_html = ""
    for i, c in enumerate(competitions, 1):
        name = c.get("name", "未知")
        host = c.get("host", "")
        location = c.get("location", "")
        prize = c.get("prize", "")
        deadline = c.get("deadline", "未知")
        apply_url = c.get("apply_url", "")
        source = c.get("source", "")
        status = c.get("status", "")

        apply_link = f'<a href="{apply_url}" style="color:#0066cc;text-decoration:none;">点击报名</a>' if apply_url else "暂无链接"

        status_badge = ""
        if "CLOSING SOON" in status or "即将截止" in status:
            status_badge = '<span style="background:#ff4d4f;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;">即将截止</span>'

        rows_html += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:12px 8px;vertical-align:top;">
                <div style="font-weight:bold;font-size:15px;color:#1a1a1a;margin-bottom:4px;">
                    {i}. {name} {status_badge}
                </div>
                <div style="font-size:13px;color:#666;line-height:1.6;">
                    {'主办方：' + host if host else ''}
                    {' | 地点：' + location if location else ''}
                    {' | 形式：' + c.get('format', '') if c.get('format') else ''}
                </div>
                <div style="font-size:13px;color:#666;margin-top:2px;">
                    💰 奖金：{prize or '未知'}
                    &nbsp;|&nbsp;
                    ⏰ 报名截止：<span style="color:#d4380d;font-weight:bold;">{deadline or '未知'}</span>
                </div>
                <div style="font-size:13px;margin-top:4px;">
                    🔗 {apply_link}
                    &nbsp;|&nbsp;
                    <span style="color:#999;">来源：{source}</span>
                </div>
            </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin:0; padding:20px; background:#f5f5f5; }}
    .container {{ max-width:680px; margin:0 auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08); }}
    .header {{ background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:#fff; padding:24px 28px; }}
    .header h1 {{ margin:0; font-size:22px; }}
    .header p {{ margin:6px 0 0; opacity:0.9; font-size:14px; }}
    .content {{ padding:20px 28px; }}
    .summary {{ background:#f0f5ff; border-left:4px solid #667eea; padding:12px 16px; margin-bottom:16px; border-radius:4px; font-size:14px; }}
    table {{ width:100%; border-collapse:collapse; }}
    .footer {{ padding:16px 28px; background:#fafafa; font-size:12px; color:#999; text-align:center; border-top:1px solid #eee; }}
    .tip {{ background:#fff7e6; border:1px solid #ffd591; padding:10px 14px; border-radius:4px; font-size:13px; color:#ad6800; margin-top:16px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🚀 黑客松雷达</h1>
        <p>发现 {len(competitions)} 个新的黑客松/竞赛机会 · {now}</p>
    </div>
    <div class="content">
        <div class="summary">
            本次扫描发现 <strong>{len(competitions)}</strong> 个未推送过的比赛机会。
            点击"点击报名"可直接跳转报名页面。报名后把规则文档发给我，我会用 competition-award-pathfinder 方法论帮你分析最优获奖路径并生成 idea + 路演稿。
        </div>
        <table>
            {rows_html}
        </table>
        <div class="tip">
            💡 <strong>提示：</strong>报名后，将比赛规则文档/链接回复给我，我会自动分析赛道、评审标准、硬门槛，输出3个针对性 idea 和路演文档框架，最大化获奖概率。
        </div>
    </div>
    <div class="footer">
        黑客松雷达 · 每天 9:00 / 20:00 自动扫描推送<br>
        数据来源：HackHQ 等公开平台 · 仅供参考，请以官方信息为准
    </div>
</div>
</body>
</html>"""
    return html


def generate_plain(competitions: list) -> str:
    lines = [f"黑客松雷达 - 发现 {len(competitions)} 个新比赛", "=" * 40, ""]
    for i, c in enumerate(competitions, 1):
        lines.append(f"{i}. {c.get('name', '未知')}")
        if c.get("host"):
            lines.append(f"   主办方：{c['host']}")
        if c.get("location"):
            lines.append(f"   地点：{c['location']}")
        if c.get("prize"):
            lines.append(f"   奖金：{c['prize']}")
        lines.append(f"   截止：{c.get('deadline', '未知')}")
        if c.get("apply_url"):
            lines.append(f"   报名：{c['apply_url']}")
        lines.append(f"   来源：{c.get('source', '')}")
        lines.append("")
    lines.append("报名后回复规则文档，我将帮你分析获奖路径并生成 idea + 路演稿。")
    return "\n".join(lines)


def main():
    if not NEW_FILE.exists():
        print("错误：latest_new.json 不存在", file=sys.stderr)
        sys.exit(1)

    with open(NEW_FILE, "r", encoding="utf-8") as f:
        competitions = json.load(f)

    if not competitions:
        print("没有新增比赛")
        return

    html = generate_html(competitions)
    plain = generate_plain(competitions)

    html_file = WORK_DIR / "email_content.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

    plain_file = WORK_DIR / "email_content.txt"
    with open(plain_file, "w", encoding="utf-8") as f:
        f.write(plain)

    print(f"已生成邮件内容：{len(competitions)} 个比赛")
    print(f"HTML: {html_file}")
    print(f"纯文本: {plain_file}")


if __name__ == "__main__":
    main()
