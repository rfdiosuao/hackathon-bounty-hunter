#!/usr/bin/env python3
"""
黑客松雷达 - 飞书消息推送脚本
读取 latest_new.json，通过 lark-cli 发送飞书消息
"""

import json
import subprocess
import sys
from pathlib import Path

WORK_DIR = Path(__file__).parent
CONFIG_FILE = WORK_DIR / "config.json"
NEW_FILE = WORK_DIR / "latest_new.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_markdown(competitions: list) -> str:
    """构建飞书 markdown 消息"""
    lines = [f"🚀 **黑客松雷达 - 发现 {len(competitions)} 个新比赛**", ""]

    for i, c in enumerate(competitions[:10], 1):
        name = c.get("name", "未知")
        host = c.get("host", "")
        location = c.get("location", "")
        prize = c.get("prize", "")
        deadline = c.get("deadline", "未知")
        apply_url = c.get("apply_url", "")
        source = c.get("source", "")
        status = c.get("status", "")

        status_tag = ""
        if "CLOSING SOON" in status or "即将截止" in status:
            status_tag = " 🔥即将截止"

        lines.append(f"**{i}. {name}**{status_tag}")
        info_parts = []
        if host:
            info_parts.append(f"主办方：{host}")
        if location:
            info_parts.append(f"地点：{location}")
        if prize:
            info_parts.append(f"奖金：{prize}")
        if info_parts:
            lines.append(f"   {' | '.join(info_parts)}")
        lines.append(f"   ⏰ 截止：{deadline}")
        if apply_url:
            lines.append(f"   🔗 [点击报名]({apply_url})")
        lines.append(f"   📌 来源：{source}")
        lines.append("")

    if len(competitions) > 10:
        lines.append(f"*还有 {len(competitions) - 10} 个比赛，详情请查收邮件*")
        lines.append("")

    lines.append("---")
    lines.append("💡 报名后把规则文档发给我，我会用 **competition-award-pathfinder** 方法论帮你分析最优获奖路径，输出3个针对性 idea + 路演稿。")

    return "\n".join(lines)


def send_feishu(open_id: str, markdown: str) -> bool:
    """通过 lark-cli 发送飞书消息"""
    try:
        cmd = [
            "lark-cli", "im", "+messages-send",
            "--user-id", open_id,
            "--markdown", markdown,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            resp = json.loads(result.stdout)
            if resp.get("ok"):
                print(f"飞书消息发送成功，message_id: {resp['data']['message_id']}")
                return True
            else:
                print(f"飞书消息发送失败: {resp}", file=sys.stderr)
                return False
        else:
            print(f"lark-cli 执行失败: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"飞书发送异常: {e}", file=sys.stderr)
        return False


def main():
    config = load_config()
    feishu_config = config.get("feishu", {})
    open_id = feishu_config.get("open_id", "")

    if not open_id:
        print("错误：未配置飞书 open_id", file=sys.stderr)
        sys.exit(1)

    if not NEW_FILE.exists():
        print("错误：latest_new.json 不存在", file=sys.stderr)
        sys.exit(1)

    with open(NEW_FILE, "r", encoding="utf-8") as f:
        competitions = json.load(f)

    if not competitions:
        print("没有新增比赛，不发送飞书消息")
        return

    markdown = build_markdown(competitions)
    print(f"准备发送 {len(competitions)} 个比赛到飞书...")

    success = send_feishu(open_id, markdown)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
