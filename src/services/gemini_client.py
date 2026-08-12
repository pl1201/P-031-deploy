"""Gọi Gemini dùng chung — structured output + xoay vòng key.

Tách từ `target_assistant.py` khi có điểm dùng thứ hai (`menu_coach.py`,
`AGT-13`) — tránh trùng logic xoay vòng key ở hai nơi. Module thuần hạ tầng,
không chứa logic lâm sàng nào; caller chịu trách nhiệm về prompt/schema.
"""

from __future__ import annotations

import logging
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

_SchemaT = TypeVar("_SchemaT", bound=BaseModel)


def call_gemini(
    prompt: str,
    system_prompt: str,
    schema: type[_SchemaT],
    settings: Settings | None = None,
) -> _SchemaT:
    settings = settings or get_settings()
    keys = settings.gemini_keys()
    if not keys:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY nào trong .env")

    config = types.GenerateContentConfig(
        temperature=settings.llm_temperature,
        response_mime_type="application/json",
        response_schema=schema,
        system_instruction=system_prompt,
    )

    last_error: errors.APIError | None = None
    for i, key in enumerate(keys):
        client = genai.Client(api_key=key)
        try:
            resp = client.models.generate_content(model=settings.gemini_model, contents=prompt, config=config)
        except errors.ClientError as exc:
            if exc.code == 429 and i < len(keys) - 1:
                logger.warning("Gemini key #%d het quota (429), doi key ke tiep.", i + 1)
                last_error = exc
                continue
            raise
        parsed = resp.parsed
        if isinstance(parsed, schema):
            return parsed
        return schema.model_validate_json(resp.text or "{}")
    raise RuntimeError("Tất cả key Gemini đều hết quota") from last_error
