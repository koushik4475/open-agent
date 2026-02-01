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

SUMMARIZE_SYSTEM = """You are a precise summarizer. Your job:
1. Extract the KEY points only.
2. Remove all filler, repetition, and tangential details.
3. Output a clean bulleted list followed by a 1-2 sentence TL;DR.
4. Be factual — do not add information that isn't in the source."""


async def summarize_text(prompt: str, llm: LLMClient | None = None) -> str:
    """
    Summarize the text contained in the prompt.
    If no LLM client is passed, creates one.
    """
    if llm is None:
        llm = LLMClient()

    logger.info("Running summarization")
    return await llm.generate(prompt, system=SUMMARIZE_SYSTEM)
