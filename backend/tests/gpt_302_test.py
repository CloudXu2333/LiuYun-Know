import os
import sys
import json
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://api.302.ai"


def chat_gpt_52(prompt: str, model: str = "gpt-5.2") -> str:
    """
    调用 302.ai 的 GPT API
    你开通的模型：
    - gpt-5.2 (GPT 5.2)
    - gpt-5.1 (GPT 5.1)
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
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
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
        reply = chat_gpt_52(prompt)
    except Exception as exc:
        print(f"调用 302 GPT-5.2 失败: {exc}")
        sys.exit(1)

    print("User:", prompt)
    print("GPT-5.2:", reply)


if __name__ == "__main__":
    main()

