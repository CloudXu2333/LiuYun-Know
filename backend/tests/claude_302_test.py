import os
import sys
import json
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://api.302.ai"


def chat_claude(prompt: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    """
    调用 302.ai 的 Claude API
    
    你开通的模型：
    - claude-opus-4-5-20251101 (Claude 4.5 Opus)
    - claude-sonnet-4-5-20250929 (最新 Claude 4.5 Sonnet)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("环境变量 OPENAI_API_KEY 未设置")

    url = f"{API_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    
    # 详细错误信息
    if resp.status_code != 200:
        print(f"\n错误状态码: {resp.status_code}")
        print(f"错误响应: {resp.text}")
        resp.raise_for_status()

    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        return json.dumps(data, ensure_ascii=False)
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        return json.dumps(data, ensure_ascii=False)
    return content


def main() -> None:
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "用一句话简单自我介绍一下。"

    try:
        reply = chat_claude(prompt)
    except Exception as exc:
        print(f"调用 302 Claude 失败: {exc}")
        sys.exit(1)

    print("User:", prompt)
    print("Claude:", reply)


if __name__ == "__main__":
    main()
