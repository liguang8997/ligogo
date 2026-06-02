"""
DeepSeek API 客户端 (Anthropic 兼容接口)
"""
import json
import httpx
from app.core.config import get_settings

settings = get_settings()


class DeepSeekClient:
    def __init__(self, model: str = "pro"):
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.DEEPSEEK_PRO_MODEL if model == "pro" else settings.DEEPSEEK_FLASH_MODEL

    async def chat(self, messages: list[dict], system: str = None, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        """非流式对话"""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            data = resp.json()
            if "error" in data:
                raise Exception(f"API Error: {data['error']}")
            # DeepSeek returns multiple content blocks (thinking + text)
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            # Fallback: return last content block
            if data.get("content"):
                return str(data["content"][-1])
            raise Exception(f"Unexpected API response: {data}")

    async def chat_stream(self, messages: list[dict], system: str = None, max_tokens: int = 2048, temperature: float = 0.7):
        """流式对话，yield 文本块"""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            if chunk.get("type") == "content_block_delta":
                                text = chunk.get("delta", {}).get("text", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue
