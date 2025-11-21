import os
import httpx
from typing import List

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def ask_ai(messages: List[dict]) -> str:
    if not OPENROUTER_API_KEY:
        # fallback simple behavior
        # Return joined user content or a placeholder
        for m in reversed(messages):
            if m.get("role") == "user":
                return "\n".join(["Tell me about your experience."] * 5)
        return "Fallback response"

    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        content = data.get("choices", [])[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("AI returned empty response")
        return content
