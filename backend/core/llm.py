import httpx
from fastapi import HTTPException

from core.config import GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL


def call_groq(messages: list, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
