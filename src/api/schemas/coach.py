"""API schemas for AI financial coach endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class CoachChatMessage(BaseModel):
    """One message in an AI coach chat conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class CoachChatRequest(BaseModel):
    """Request body for sending a message to the AI financial coach chat.

    Carries the full conversation history, including the newest user
    message — the frontend keeps history in React state only and resends
    it every call (stateless backend, per the ephemeral-chat design).
    """

    messages: list[CoachChatMessage] = Field(min_length=1)


class CoachChatResponse(BaseModel):
    """Response body containing the assistant's reply for this turn."""

    reply: str
