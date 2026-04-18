from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from tripplanner.core.config import get_settings
from tripplanner.web.services.llm import LLMClient

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    plan_context: str | None = None


@router.post("")
async def chat_endpoint(req: ChatRequest) -> dict[str, str]:
    """Send a chat message and get a response."""
    settings = get_settings()

    if not settings.openai_api_key:
        return {"response": "Chat is not configured. Please set OPENAI_API_KEY."}

    async with LLMClient(settings) as client:
        response = await client.chat(req.messages, req.plan_context)
    return {"response": response}


@router.get("/stream")
async def chat_stream_endpoint(
    messages: str = "[]",
    plan_context: str | None = None,
) -> EventSourceResponse:
    """Stream chat response tokens via SSE."""

    async def event_generator():
        settings = get_settings()
        if not settings.openai_api_key:
            yield {"event": "error", "data": json.dumps({"error": "Chat not configured"})}
            return

        try:
            parsed_messages = json.loads(messages)
        except json.JSONDecodeError:
            yield {"event": "error", "data": json.dumps({"error": "Invalid messages"})}
            return

        async with LLMClient(settings) as client:
            async for token in client.chat_stream(parsed_messages, plan_context):
                yield {"event": "message", "data": json.dumps({"content": token})}

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
