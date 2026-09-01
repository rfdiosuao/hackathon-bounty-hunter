# 快速开始

## 5分钟跑通黑客松雷达

### 1. 克隆项目

```bash
git clone https://github.com/rfdiosuao/hackathon-bounty-hunter.git
cd hackathon-bounty-hunter
```

### 2. 安装依赖

```bash
pip install requests beautifulsoup4
# 可选：阿里云短信
pip install alibabacloud-dysmsapi20170525 alibabacloud-tea-openapi
```

### 3. 配置

```bash
cp config/config.example.json 01-radar/config.json
# 编辑 01-radar/config.json，填入你的配置
```

最少需要配置：
- `user.location`：你的城市（如"上海"）
- `notify.feishu.open_id`：飞书 open_id（推荐，零成本）

获取飞书 open_id：
```bash
lark-cli contact +get-user
# 输出中的 open_id 字段
```

### 4. 运行一次扫描

```bash
cd 01-radar
python3 fetch_hackathons.py
python3 send_feishu.py
```

你会收到一条飞书消息，包含最新的黑客松列表。

### 5. 设置定时任务

使用系统 cron：
```bash
crontab -e
# 添加：每天9点和20点执行
0 9,20 * * * cd /path/to/hackathon-bounty-hunter/01-radar && python3 fetch_hackathons.py && python3 send_feishu.py
```

或使用豆包定时任务（推荐，支持AI搜索补充）：
在豆包中说"创建定时任务，每天9点和20点运行黑客松雷达扫描"。

---

## 配置多平台推送

### 飞书（推荐，免费）

1. 安装 lark-cli 并登录
2. 获取 open_id：`lark-cli contact +get-user`
3. 填入 config.json 的 `notify.feishu.open_id`

### 邮箱（QQ邮箱示例）

1. 登录 [mail.qq.com](https://mail.qq.com) → 设置 → 账户
2. 开启「POP3/SMTP服务」，生成授权码
3. 填入 config.json：
   - `notify.email.smtp.username`: 你的QQ邮箱
   - `notify.email.smtp.password`: 16位授权码
   - `notify.email.to`: 接收邮箱

### 短信（阿里云）

1. 注册阿里云，开通短信服务
2. 创建 AccessKey（建议用RAM子账号）
3. 申请短信签名和模板
4. 填入 config.json 的 `notify.sms` 部分

### 微信（企业微信机器人）

1. 在企业微信群添加机器人，获取 webhook URL
2. 填入 `notify.wechat.webhook_url`

---

## 配置信息源

在 config.json 的 `sources` 部分启用/禁用信息源：

| 来源 | 说明 | 状态 |
|---|---|---|
| `hackhq` | GitHub 结构化全球黑客松列表 | ✅ 可用 |
| `web_search` | AI 全网搜索补充（小红书/CSDN/官网等） | ✅ 可用 |
| `devpost` | 全球最大黑客松平台 | ⚠️ 有反爬，待优化 |
| `xiaohongshu` | 小红书博主图文 | 🔧 需浏览器+OCR |
| `douyin` | 抖音赛事信息 | 🔧 需浏览器 |
| `bilibili` | B站赛事视频/动态 | 🔧 待开发 |
| `discord` | Discord 社群情报 | 🔧 需机器人 |
| `luma` | Luma 活动列表 | 🔧 待开发 |
| `custom_urls` | 自定义监控URL列表 | ✅ 可配置 |

启用 `web_search` 后，系统会自动搜索：
- "2026 黑客松 报名 截止"
- "AI 竞赛 黑客松 奖金"
- "你的城市 黑客松 线下"

---

## 基于位置的智能推荐

配置 `user.location` 后，系统会：
1. 优先推送你所在城市及周边的线下比赛
2. 计算交通成本（高铁/飞机），过滤超出预算的比赛
3. 线上比赛不受位置限制，全部推送

配置 `filter.max_distance_km` 控制推送范围（默认300km）。

---

## 下一步

- 阅读 [工作流总览](../README.md) 了解七阶段方法论
- 查看 [配置说明](CONFIGURATION.md) 了解所有配置项
- 报名比赛后，用 competition-award-pathfinder 分析获奖路径
