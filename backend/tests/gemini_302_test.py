import os
import sys
import json
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://api.302.ai"


def chat_gemini(prompt: str, model: str = "gemini-2.5-pro", stream: bool = False) -> str:
    """
    调用 302.ai 的 Gemini API
    你开通的模型：
    - gemini-2.5-pro (Gemini 2.5 Pro)
    - gemini-3-pro-preview (Gemini 3.0 Pro)
    
    参数：
    - stream: 是否使用流式输出
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
        "stream": stream,
    }

    if stream:
        # 流式输出
        resp = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        resp.raise_for_status()
        
        full_content = ""
        for line in resp.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # 移除 'data: ' 前缀
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get('choices', [])
                        if choices and len(choices) > 0:
                            delta = choices[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                full_content += content
                    except json.JSONDecodeError:
                        pass
        print()  # 换行
        return full_content
    else:
        # 非流式输出
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # 调试：显示状态码
        if resp.status_code != 200:
            print(f"\n错误状态码: {resp.status_code}")
            print(f"错误响应: {resp.text}")
            resp.raise_for_status()

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            print(f"\n调试 - 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return "未获取到回复"
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            return json.dumps(data, ensure_ascii=False)
        return content


def main() -> None:
    # 解析参数
    args = sys.argv[1:]
    stream_mode = False
    
    if '--stream' in args or '-s' in args:
        stream_mode = True
        args = [a for a in args if a not in ('--stream', '-s')]
    
    if args:
        prompt = " ".join(args)
    else:
        prompt = "用一句话简单自我介绍一下。"

    try:
        print("User:", prompt)
        if stream_mode:
            print("Gemini: ", end='', flush=True)
            chat_gemini(prompt, stream=True)
        else:
            reply = chat_gemini(prompt, stream=False)
            print("Gemini:", reply)
    except Exception as exc:
        print(f"\n调用 302 Gemini 失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
