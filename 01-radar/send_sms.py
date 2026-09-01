#!/usr/bin/env python3
"""
黑客松雷达 - 短信发送脚本
支持阿里云短信服务
配置：config.json 中的 sms 字段
"""

import json
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


def send_aliyun_sms(phone: str, sign_name: str, template_code: str,
                    template_param: dict, access_key_id: str,
                    access_key_secret: str) -> bool:
    """通过阿里云短信服务发送短信"""
    try:
        from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
        from alibabacloud_tea_util import models as util_models

        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "dysmsapi.aliyuncs.com"
        client = Dysmsapi20170525Client(config)

        request = dysmsapi_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=sign_name,
            template_code=template_code,
            template_param=json.dumps(template_param, ensure_ascii=False),
        )
        runtime = util_models.RuntimeOptions()
        response = client.send_sms_with_options(request, runtime)

        body = response.body
        if body.code == "OK":
            print(f"短信发送成功 → {phone}")
            return True
        else:
            print(f"短信发送失败: code={body.code}, message={body.message}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"短信发送异常: {e}", file=sys.stderr)
        return False


def build_sms_content(competitions: list) -> tuple:
    count = len(competitions)
    upcoming = None
    for c in competitions:
        if c.get("deadline"):
            upcoming = c
            break

    deadline = upcoming["deadline"][:12] if upcoming and upcoming.get("deadline") else "近期"
    first_name = competitions[0]["name"][:20] if competitions else ""

    template_param = {
        "count": str(count),
        "deadline": deadline,
        "name": first_name,
    }

    preview = f"【黑客松雷达】发现{count}条新比赛，最近截止{deadline}，详情查收邮件。"
    return template_param, preview


def main():
    config = load_config()
    sms_config = config.get("sms", {})

    if not sms_config.get("enabled", False):
        print("短信未启用（sms.enabled=false）")
        return

    provider = sms_config.get("provider", "aliyun")
    phone = sms_config.get("phone", "")
    sign_name = sms_config.get("sign_name", "")
    template_code = sms_config.get("template_code", "")
    access_key_id = sms_config.get("access_key_id", "")
    access_key_secret = sms_config.get("access_key_secret", "")

    missing = []
    if not phone:
        missing.append("phone(接收手机号)")
    if not sign_name:
        missing.append("sign_name(短信签名)")
    if not template_code:
        missing.append("template_code(模板ID)")
    if not access_key_id:
        missing.append("access_key_id")
    if not access_key_secret:
        missing.append("access_key_secret")

    if missing:
        print(f"短信配置缺失: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if not NEW_FILE.exists():
        print("无新增比赛数据", file=sys.stderr)
        sys.exit(1)

    with open(NEW_FILE, "r", encoding="utf-8") as f:
        competitions = json.load(f)

    if not competitions:
        print("没有新增比赛，不发短信")
        return

    template_param, preview = build_sms_content(competitions)
    print(f"短信内容预览: {preview}")

    if provider == "aliyun":
        success = send_aliyun_sms(
            phone=phone,
            sign_name=sign_name,
            template_code=template_code,
            template_param=template_param,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        sys.exit(0 if success else 1)
    else:
        print(f"不支持的短信服务商: {provider}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
