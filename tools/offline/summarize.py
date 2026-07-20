# openagent/tools/offline/summarize.py
"""
Text Summarization Tool (Offline).

Uses the local LLM to summarize whatever text is in the prompt.
Works on:
  - Pasted text
  - Extracted file content
  - Previous web fetch results

This is a "tool" in name but really it's just a well-crafted
prompt sent to the LLM. The power is in the prompt engineering.
"""

from __future__ import annotations
import logging

from openagent.core.llm import LLMClient

logger = logging.getLogger("openagent.tools.summarize")

SUMMARIZE_SYSTEM = """You are a precise summarizer. Output a structured Markdown summary in exactly this shape:

### Key points
- 3-8 self-contained bullets with the essential facts. Preserve concrete names, numbers, and dates. Bold the most important term in each bullet.

### TL;DR
> One or two sentences capturing the core message.

Rules:
- Strictly factual — never add information absent from the source.
- Drop filler, repetition, and tangents.
- Summarize in the same language as the source text.
- If the text is too short or unclear to summarize, say so briefly instead of padding."""


async def summarize_text(prompt: str, llm: LLMClient | None = None) -> str:
    """
    Summarize the text contained in the prompt.
    If no LLM client is passed, creates one.
    """
    if llm is None:
        llm = LLMClient()

    logger.info("Running summarization")
    return await llm.generate(prompt, system=SUMMARIZE_SYSTEM)
