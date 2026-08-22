from __future__ import annotations

import re
import unicodedata


_EXPLICIT_PROMPT_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,80}"
        r"\b(?:previous|prior|above|system|developer|hidden)\b.{0,40}"
        r"\b(?:instructions?|prompt|message)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:reveal|show|print|return|expose|repeat)\b.{0,80}"
        r"\b(?:system\s+prompt|hidden\s+instructions?|developer\s+message)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:忽略|無視|覆寫|繞過).{0,40}"
        r"(?:先前|之前|以上|系統|開發者|隱藏).{0,20}"
        r"(?:指令|提示|訊息)",
        re.DOTALL,
    ),
    re.compile(
        r"(?:揭露|顯示|輸出|回傳).{0,40}"
        r"(?:系統提示|隱藏指令|開發者訊息)",
        re.DOTALL,
    ),
)


def contains_explicit_prompt_injection(*values: object) -> bool:
    normalized = "\n".join(
        unicodedata.normalize("NFKC", str(value)).casefold()
        for value in values
        if value is not None
    )
    return any(pattern.search(normalized) for pattern in _EXPLICIT_PROMPT_INJECTION_PATTERNS)
