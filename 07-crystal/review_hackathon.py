#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑客松赏金猎人 - 复盘结晶模块
比赛结束后，引导结构化复盘，自动分析短板，生成复盘文档，自动提交 PR 到总仓库。
"""
import json
import os
import sys
import datetime
import requests
from pathlib import Path

# ============================================================
# 配置
# ============================================================
CONFIG_PATH = Path(__file__).parent / "config.json"
EXAMPLE_CONFIG_PATH = Path(__file__).parent / "config.example.json"
REVIEWS_DIR = "reviews"

DEFAULT_CONFIG = {
    "github_token": "",
    "github_owner": "rfdiosuao",
    "github_repo": "hackathon-bounty-hunter",
    "github_branch": "main",
    "llm_api_key": "",
    "llm_base_url": "https://api.openai.com/v1",
    "llm_model": "gpt-4o-mini"
}

# ============================================================
# 维度定义
# ============================================================
DIMENSIONS = [
    {"key": "idea_innovation", "name": "idea 创新性", "module": "03-pathfinder", "advice": "用「反惯性·多视角·闭环验证」提示词重新生成 idea，至少做 3 个差异化方向对比，不要停在第一个想法。"},
    {"key": "idea_practicality", "name": "idea 实用性", "module": "02-compass", "advice": "动手前先做 5 个用户访谈，验证是真需求还是伪需求。用 competition-award-pathfinder 分析比赛评分维度，倒推项目方向。"},
    {"key": "ui_design", "name": "UI 设计", "module": "04-arsenal / 05-stage", "advice": "参考秒哒获奖作品的 UI 美学模块，先确定风格基调（民国复古/暗黑国风/水彩治愈/星空数据），做完整设计稿再开发，不要边写边想。"},
    {"key": "ux_interaction", "name": "交互体验", "module": "05-stage UX_INTERACTION", "advice": "参考交互逻辑和交互动作蒸馏模块，每个按钮都要有反馈，每个状态都要有过渡，错误场景要友好处理。"},
    {"key": "tech_completion", "name": "技术完成度", "module": "05-stage PRODUCTION_FLOW", "advice": "按制作流程倒推：先做图片资产，再搭框架，最后填充。48 小时内只做核心 demo，砍掉所有非必要功能。"},
    {"key": "pitch_story", "name": "路演讲故事", "module": "06-sprint", "advice": "用「痛点→方案→演示→愿景→团队」五段式框架。开场 30 秒讲一个真实故事，演示 2 分钟，数据 30 秒，愿景 30 秒。"},
    {"key": "time_management", "name": "时间管理", "module": "倒推时间线模板", "advice": "比赛开始就用倒推时间线，提前 2 周锁定功能范围，最后一周只做优化和测试，不加新功能。"}
]

FAIL_REASONS = [
    {"key": "idea_not_innovative", "name": "idea 不够创新", "dimension": "idea_innovation"},
    {"key": "idea_not_useful", "name": "idea 不实用/伪需求", "dimension": "idea_practicality"},
    {"key": "ui_bad", "name": "UI 不够炸", "dimension": "ui_design"},
    {"key": "ux_bad", "name": "交互体验差", "dimension": "ux_interaction"},
    {"key": "incomplete", "name": "功能不完整/bug 多", "dimension": "tech_completion"},
    {"key": "pitch_bad", "name": "路演没讲好", "dimension": "pitch_story"},
    {"key": "time_not_enough", "name": "时间不够/进度失控", "dimension": "time_management"},
    {"key": "tech_hard", "name": "技术难点没攻克", "dimension": "tech_completion"},
    {"key": "team_issue", "name": "团队协作问题", "dimension": "time_management"},
    {"key": "other", "name": "其他", "dimension": None}
]

# ============================================================
# 工具函数
# ============================================================
def load_config():
    """加载配置，不存在则从 example 复制"""
    if not CONFIG_PATH.exists():
        if EXAMPLE_CONFIG_PATH.exists():
            import shutil
            shutil.copy(EXAMPLE_CONFIG_PATH, CONFIG_PATH)
            print(f"[配置] 已从 config.example.json 创建 config.json")
        else:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"[配置] 已创建默认 config.json")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ask(prompt, default=None):
    """提问，支持默认值"""
    if default:
        result = input(f"{prompt} [默认: {default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def ask_choice(prompt, choices, allow_multi=False):
    """选择题，支持多选"""
    print(f"\n{prompt}")
    for i, c in enumerate(choices, 1):
        print(f"  {i}. {c['name']}")
    if allow_multi:
        raw = input("输入序号（多选用逗号分隔，如 1,3,5）: ").strip()
        if not raw:
            return []
        indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
        return [choices[i] for i in indices if 0 <= i < len(choices)]
    else:
        while True:
            raw = input("输入序号: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(choices):
                return choices[int(raw) - 1]
            print("请输入有效序号")


def ask_score(prompt):
    """1-5 分评分"""
    while True:
        raw = input(f"{prompt} (1-5): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 5:
            return int(raw)
        print("请输入 1-5 的数字")


# ============================================================
# 问卷
# ============================================================
def run_questionnaire():
    """运行交互式复盘问卷"""
    print("\n" + "=" * 60)
    print("  🏆 黑客松赏金猎人 - 复盘结晶")
    print("  比赛结束不是终点，是下一次拿奖的起点")
    print("=" * 60 + "\n")

    review = {}

    # 1. 基本信息
    print("--- 基本信息 ---")
    review["competition_name"] = ask("比赛名称（如：2026微信小程序开发大赛）")
    review["team_name"] = ask("参赛队名/个人名")
    review["competition_date"] = ask("比赛日期（如：2026-11-20）", datetime.date.today().isoformat())
    review["project_name"] = ask("作品名称")
    review["result"] = ask("最终成绩（如：一等奖/未获奖/第8名）")
    review["result_level"] = ask_choice("获奖等级", [
        {"key": "champion", "name": "一等奖/冠军"},
        {"key": "second", "name": "二等奖/亚军"},
        {"key": "third", "name": "三等奖/季军"},
        {"key": "finalist", "name": "入围决赛但未获奖"},
        {"key": "eliminated", "name": "初赛/复赛被淘汰"},
        {"key": "not_submitted", "name": "未完成/未提交"}
    ])["key"]

    # 2. 七维度自评
    print("\n--- 七维度自评（1=很差，5=很好）---")
    review["scores"] = {}
    for dim in DIMENSIONS:
        review["scores"][dim["key"]] = ask_score(f"  {dim['name']}")

    # 3. 失败原因
    print("\n--- 失败/不足原因（可多选）---")
    selected = ask_choice("哪些方面导致了成绩不理想？", FAIL_REASONS, allow_multi=True)
    review["fail_reasons"] = [r["key"] for r in selected]
    if any(r["key"] == "other" for r in selected):
        review["fail_reason_other"] = ask("请说明其他原因")

    # 4. 评委反馈
    print("\n--- 评委反馈（如有）---")
    review["judge_feedback"] = ask("评委说了什么/打分情况/现场反应（没有就填无）", "无")

    # 5. 做对了什么
    print("\n--- 可复用经验 ---")
    review["what_worked"] = ask("这次哪些做法有效，下次可以沿用？（尽量具体）")

    # 6. 下次改进 Top3
    print("\n--- 下次改进计划 ---")
    review["improvement_1"] = ask("最想改进的第 1 件事")
    review["improvement_2"] = ask("最想改进的第 2 件事", "无")
    review["improvement_3"] = ask("最想改进的第 3 件事", "无")

    return review


# ============================================================
# 分析引擎
# ============================================================
def analyze(review):
    """根据自评和失败原因，分析短板并生成建议"""
    scores = review["scores"]

    # 找出最低分的 2 个维度
    sorted_dims = sorted(DIMENSIONS, key=lambda d: scores[d["key"]])
    weakest = sorted_dims[:2]

    # 关联失败原因到维度
    fail_dimensions = set()
    for reason_key in review["fail_reasons"]:
        for fr in FAIL_REASONS:
            if fr["key"] == reason_key and fr["dimension"]:
                fail_dimensions.add(fr["dimension"])

    # 生成建议
    suggestions = []
    for dim in weakest:
        suggestions.append({
            "dimension": dim["name"],
            "score": scores[dim["key"]],
            "module": dim["module"],
            "advice": dim["advice"]
        })

    # 如果失败原因指向的维度不在最低分里，也加进去
    for dim in DIMENSIONS:
        if dim["key"] in fail_dimensions and dim not in weakest:
            suggestions.append({
                "dimension": dim["name"],
                "score": scores[dim["key"]],
                "module": dim["module"],
                "advice": dim["advice"]
            })

    return {
        "weakest_dimensions": [d["name"] for d in weakest],
        "suggestions": suggestions,
        "fail_dimensions": [d["name"] for d in DIMENSIONS if d["key"] in fail_dimensions]
    }


# ============================================================
# 文档生成
# ============================================================
def generate_review_doc(review, analysis):
    """生成 Markdown 复盘文档"""
    scores = review["scores"]
    date_str = review["competition_date"]
    team_slug = review["team_name"].replace(" ", "-").replace("/", "-")
    comp_slug = review["competition_name"].replace(" ", "-").replace("/", "-")

    # 评分文字版雷达图
    score_bars = []
    for dim in DIMENSIONS:
        s = scores[dim["key"]]
        bar = "█" * s + "░" * (5 - s)
        score_bars.append(f"| {dim['name']} | {bar} | {s}/5 |")

    # 失败原因名称
    fail_names = []
    for rk in review["fail_reasons"]:
        for fr in FAIL_REASONS:
            if fr["key"] == rk:
                fail_names.append(fr["name"])

    # 建议
    suggestion_lines = []
    for i, sug in enumerate(analysis["suggestions"], 1):
        suggestion_lines.append(
            f"**{i}. {sug['dimension']}**（得分 {sug['score']}/5）\n"
            f"   - 指向模块：`{sug['module']}`\n"
            f"   - 建议：{sug['advice']}"
        )

    doc = f"""# 复盘：{review['competition_name']} - {review['team_name']}

> 复盘日期：{datetime.date.today().isoformat()}
> 比赛日期：{date_str}
> 作品名称：{review['project_name']}
> 最终成绩：{review['result']}

---

## 一、比赛基本信息

| 项目 | 内容 |
|---|---|
| 比赛名称 | {review['competition_name']} |
| 参赛队名 | {review['team_name']} |
| 作品名称 | {review['project_name']} |
| 比赛日期 | {date_str} |
| 最终成绩 | {review['result']} |

---

## 二、七维度自评

| 维度 | 评分 | 分数 |
|---|---|---|
{chr(10).join(score_bars)}

**最薄弱的 2 个维度**：{', '.join(analysis['weakest_dimensions'])}

---

## 三、失败/不足原因

{chr(10).join([f'- {n}' for n in fail_names]) if fail_names else '- 无'}

{review.get('fail_reason_other', '') and f'**其他说明**：{review["fail_reason_other"]}' or ''}

---

## 四、评委反馈

{review['judge_feedback']}

---

## 五、针对性优化建议

{chr(10).join(suggestion_lines)}

---

## 六、可复用经验（这次做对了什么）

{review['what_worked']}

---

## 七、下次改进计划

1. {review['improvement_1']}
2. {review['improvement_2']}
3. {review['improvement_3']}

---

## 八、给社区的话

> 这份复盘来自真实参赛经历，希望能帮助后来者少走弯路。
> 如果你也有复盘想分享，运行 `python3 07-crystal/review_hackathon.py` 即可自动提交 PR。

---

*由黑客松赏金猎人 · 复盘结晶模块自动生成*
"""
    return doc


# ============================================================
# GitHub PR 自动提交
# ============================================================
def submit_pr(config, review, doc_content, analysis):
    """自动创建分支、提交文件、创建 PR"""
    token = config.get("github_token", "")
    owner = config.get("github_owner", "rfdiosuao")
    repo = config.get("github_repo", "hackathon-bounty-hunter")
    base_branch = config.get("github_branch", "main")

    if not token:
        print("\n[警告] 未配置 github_token，跳过自动提 PR")
        print("请编辑 07-crystal/config.json 填入 GitHub Personal Access Token")
        print("复盘文档已保存到本地，你可以手动提交")
        return None

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    api_base = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        # 1. 获取 base branch 的 SHA
        print("[PR] 获取主分支信息...")
        r = requests.get(f"{api_base}/git/ref/heads/{base_branch}", headers=headers, timeout=10)
        r.raise_for_status()
        base_sha = r.json()["object"]["sha"]

        # 2. 创建新分支
        date_str = datetime.date.today().isoformat()
        team_slug = review["team_name"].replace(" ", "-").replace("/", "-")[:30]
        comp_slug = review["competition_name"].replace(" ", "-").replace("/", "-")[:30]
        branch_name = f"review/{comp_slug}-{team_slug}-{date_str}"
        branch_name = branch_name.lower().replace("_", "-")
        print(f"[PR] 创建分支: {branch_name}")
        r = requests.post(f"{api_base}/git/refs", headers=headers, timeout=10, json={
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        })
        if r.status_code not in (200, 201):
            # 分支可能已存在，尝试获取
            r2 = requests.get(f"{api_base}/git/ref/heads/{branch_name}", headers=headers, timeout=10)
            if r2.status_code == 200:
                print(f"[PR] 分支已存在，直接使用")
            else:
                r.raise_for_status()

        # 3. 提交复盘文档
        date_str = review["competition_date"]
        file_path = f"{REVIEWS_DIR}/{date_str}-{comp_slug}-{team_slug}.md"
        file_path = file_path.lower().replace(" ", "-").replace("_", "-")
        print(f"[PR] 提交复盘文档: {file_path}")
        r = requests.put(f"{api_base}/contents/{file_path}", headers=headers, timeout=15, json={
            "message": f"复盘：{review['competition_name']} - {review['team_name']}",
            "content": _b64encode(doc_content),
            "branch": branch_name
        })
        r.raise_for_status()

        # 4. 创建 PR
        pr_title = f"复盘：{review['competition_name']} - {review['team_name']}"
        pr_body = f"""## 复盘摘要

- **比赛**：{review['competition_name']}
- **参赛队**：{review['team_name']}
- **作品**：{review['project_name']}
- **成绩**：{review['result']}
- **最薄弱维度**：{', '.join(analysis['weakest_dimensions'])}

## 优化建议

{chr(10).join([f"- **{s['dimension']}**：{s['advice'][:80]}..." for s in analysis['suggestions']])}

## 可复用经验

{review['what_worked'][:200]}

---
*由黑客松赏金猎人 · 复盘结晶模块自动生成*
"""
        print("[PR] 创建 Pull Request...")
        r = requests.post(f"{api_base}/pulls", headers=headers, timeout=10, json={
            "title": pr_title,
            "head": branch_name,
            "base": base_branch,
            "body": pr_body,
            "maintainer_can_modify": True
        })
        r.raise_for_status()
        pr_data = r.json()
        print(f"\n✅ PR 创建成功！")
        print(f"   标题: {pr_title}")
        print(f"   链接: {pr_data['html_url']}")
        return pr_data["html_url"]

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ GitHub API 错误: {e}")
        if e.response is not None:
            print(f"   响应: {e.response.text[:300]}")
        return None
    except Exception as e:
        print(f"\n❌ 提交 PR 失败: {e}")
        return None


def _b64encode(s):
    import base64
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


# ============================================================
# 主流程
# ============================================================
def main():
    # 加载配置
    config = load_config()

    # 运行问卷
    review = run_questionnaire()

    # 确认信息
    print("\n" + "=" * 60)
    print("  请确认复盘信息")
    print("=" * 60)
    print(f"  比赛: {review['competition_name']}")
    print(f"  队伍: {review['team_name']}")
    print(f"  作品: {review['project_name']}")
    print(f"  成绩: {review['result']}")
    print(f"  最薄弱: {', '.join([DIMENSIONS[i]['name'] for i in sorted(range(len(DIMENSIONS)), key=lambda x: review['scores'][DIMENSIONS[x]['key']])[:2]])}")
    confirm = input("\n确认提交？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    # 分析
    print("\n[分析] 正在分析短板...")
    analysis = analyze(review)

    # 生成文档
    print("[生成] 正在生成复盘文档...")
    doc = generate_review_doc(review, analysis)

    # 保存本地
    date_str = review["competition_date"]
    team_slug = review["team_name"].replace(" ", "-").replace("/", "-")[:30]
    comp_slug = review["competition_name"].replace(" ", "-").replace("/", "-")[:30]
    local_path = Path(__file__).parent.parent / REVIEWS_DIR
    local_path.mkdir(exist_ok=True)
    filename = f"{date_str}-{comp_slug}-{team_slug}.md".lower().replace(" ", "-")
    local_file = local_path / filename
    with open(local_file, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[保存] 复盘文档已保存: {local_file}")

    # 提交 PR
    pr_url = submit_pr(config, review, doc, analysis)

    # 总结
    print("\n" + "=" * 60)
    print("  ✅ 复盘完成！")
    print("=" * 60)
    print(f"  本地文档: {local_file}")
    if pr_url:
        print(f"  PR 链接: {pr_url}")
    print(f"\n  最薄弱维度: {', '.join(analysis['weakest_dimensions'])}")
    print(f"  优化建议数: {len(analysis['suggestions'])}")
    print("\n  感谢你的复盘，这会让整个社区变得更强！")
    print("=" * 60)


if __name__ == "__main__":
    main()
