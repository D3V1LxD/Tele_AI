import asyncio
import logging
from collections import defaultdict
from typing import Any

import requests

from app.config import settings


logger = logging.getLogger(__name__)


class OpenRouterResponseError(RuntimeError):
    pass


class OpenRouterService:
    def __init__(self) -> None:
        self._conversations: dict[int, list[dict[str, Any]]] = defaultdict(list)

    @property
    def available(self) -> bool:
        return bool(settings.openrouter_api_key)

    async def ask(self, prompt: str, user_id: int | None = None) -> str:
        if not self.available:
            return "AI is not configured yet. Add OPENROUTER_API_KEY to the environment."

        conversation = self._conversations[user_id] if user_id is not None else []
        messages = [*conversation, {"role": "user", "content": prompt}]

        def generate() -> dict[str, Any]:
            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            }
            if settings.openrouter_site_url:
                headers["HTTP-Referer"] = settings.openrouter_site_url
            if settings.openrouter_app_name:
                headers["X-Title"] = settings.openrouter_app_name
            payload: dict[str, Any] = {
                "model": settings.openrouter_model,
                "messages": messages,
            }
            if settings.openrouter_reasoning:
                payload["reasoning"] = {"enabled": True}
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("error"):
                error = response_data["error"]
                message = error.get("message", "The provider returned an error") if isinstance(error, dict) else str(error)
                raise OpenRouterResponseError(message)
            choices = response_data.get("choices")
            if not choices or not isinstance(choices[0], dict) or not isinstance(choices[0].get("message"), dict):
                raise OpenRouterResponseError("The provider returned no assistant message")
            return choices[0]["message"]

        try:
            message = await asyncio.to_thread(generate)
        except OpenRouterResponseError as exc:
            logger.error("OpenRouter returned an error: %s", exc)
            return "The AI service returned an error. Please try again shortly."
        except requests.HTTPError as exc:
            logger.error("OpenRouter HTTP error: %s", exc.response.status_code if exc.response else "unknown")
            return "The AI service returned an error. Please try again shortly."
        except (requests.RequestException, TypeError, ValueError):
            logger.exception("OpenRouter request failed")
            return "I couldn't reach the AI service right now. Please try again in a few minutes."

        if user_id is not None:
            self._conversations[user_id].extend([
                {"role": "user", "content": prompt},
                {
                    "role": "assistant",
                    "content": message.get("content"),
                    "reasoning_details": message.get("reasoning_details"),
                },
            ])
            self._conversations[user_id] = self._conversations[user_id][-12:]
        return message.get("content") or "I could not generate a response."


openrouter = OpenRouterService()
gemini = openrouter
