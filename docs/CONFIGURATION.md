# 配置说明

所有配置在 `01-radar/config.json`（从 `config/config.example.json` 复制）。

## user - 用户信息

```json
{
  "name": "你的名字",
  "location": "上海",
  "skills": ["Python", "AI/ML", "前端"],
  "max_travel_cost": 500,
  "preferred_formats": ["线上", "线下"],
  "target_award_min": 1000
}
```

| 字段 | 说明 |
|---|---|
| `location` | 所在城市，用于推荐周边比赛 |
| `skills` | 技能栈，用于筛选匹配的比赛 |
| `max_travel_cost` | 最大差旅预算（元），超出则不推线下比赛 |
| `preferred_formats` | 偏好形式：线上/线下/混合 |
| `target_award_min` | 最低奖金阈值（元），低于此值不推 |

## sources - 信息源

```json
{
  "hackhq": true,
  "devpost": false,
  "web_search": true,
  "xiaohongshu": false,
  "douyin": false,
  "bilibili": false,
  "discord": false,
  "luma": false,
  "custom_urls": ["https://example.com/hackathons"]
}
```

启用 `web_search` 后，AI 会自动搜索全网信息。`custom_urls` 可添加你自己监控的页面。

## notify - 推送配置

支持多通道同时推送，至少配置一个。

### feishu - 飞书（推荐）

```json
{
  "enabled": true,
  "open_id": "ou_xxxxxxxxxxxxxxxx"
}
```

获取 open_id：运行 `lark-cli contact +get-user`

### email - 邮箱

```json
{
  "enabled": true,
  "smtp": {
    "server": "smtp.qq.com",
    "port": 465,
    "username": "you@qq.com",
    "password": "16位授权码",
    "from_email": "you@qq.com"
  },
  "to": "you@qq.com"
}
```

支持任意 SMTP 邮箱：QQ、163、Gmail、企业邮箱等。

### sms - 短信

```json
{
  "enabled": true,
  "provider": "aliyun",
  "phone": "138xxxx1234",
  "sign_name": "你的签名",
  "template_code": "SMS_xxxxxx",
  "access_key_id": "LTAIxxxx",
  "access_key_secret": "xxxx"
}
```

短信模板变量：`${count}`（新比赛数量）、`${deadline}`（最近截止时间）。

### wechat - 微信（企业微信机器人）

```json
{
  "enabled": true,
  "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx"
}
```

## schedule - 扫描时间

```json
{
  "scan_times": ["09:00", "20:00"],
  "timezone": "Asia/Shanghai"
}
```

## filter - 过滤规则

```json
{
  "max_distance_km": 300,
  "min_prize": 0,
  "exclude_keywords": ["已结束", "报名截止"],
  "preferred_keywords": ["AI", "Agent", "大模型"]
}
```

| 字段 | 说明 |
|---|---|
| `max_distance_km` | 线下比赛最大距离（公里），基于 user.location |
| `min_prize` | 最低奖金（元），0表示不限制 |
| `exclude_keywords` | 包含这些关键词的比赛不推送 |
| `preferred_keywords` | 包含这些关键词的比赛优先展示 |
