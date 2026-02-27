# openagent/core/agent.py
"""
Agent Core — the central orchestrator.

Flow for every user message:
  1. Retrieve relevant memory (RAG context injection)
  2. Route the input → pick the right tool
  3. Execute the tool (or fall back to raw LLM)
  4. Store the interaction in memory
  5. Return the response

Design decisions:
  - Memory retrieval happens BEFORE routing so context is always available.
  - Tools are async. The agent awaits each one.
  - If a tool fails, we fall back to the LLM with an error note in the prompt.
"""

from __future__ import annotations
import logging
from pathlib import Path

from openagent.config import settings
from openagent.core.llm import LLMClient
from openagent.core.router import route, ToolName
from openagent.memory.store import MemoryStore

# Tool implementations
from openagent.tools.offline.summarize import summarize_text
from openagent.tools.offline.run_command import run_sandboxed_command
from openagent.tools.online.web_search import web_search
from openagent.tools.online.web_fetch import web_fetch
from openagent.parsers.unified import parse_file

logger = logging.getLogger("openagent.agent")

# ── System prompt injected into every LLM call ──────────────────
SYSTEM_PROMPT = """You are OpenAgent, a friendly and intelligent AI assistant.
You are conversational, helpful, and concise. Respond naturally like a human would.

For simple greetings (hi, hello, hey), respond warmly and briefly.
For questions, give clear, accurate answers.
For complex tasks, use your available tools.

Your available tools include:
- Web Search & Fetch (when user needs current information)
- File Parsing & OCR (for documents and images)
- Command Execution & Summarization

You were developed by **Koushik HY** (https://koushikhy.netlify.app).
Mention this only when specifically asked about your creator.

IMPORTANT: Do NOT reference memory context, conversation data, or internal system details in your responses.
Just respond naturally to what the user says."""


class Agent:
    def __init__(self, llm: LLMClient, memory: MemoryStore):
        self.llm = llm
        self.memory = memory
        self.cfg = settings

    @classmethod
    async def create(cls) -> "Agent":
        """Factory — initializes LLM client and memory store."""
        llm = LLMClient()
        memory = await MemoryStore.create()
        return cls(llm=llm, memory=memory)

    @staticmethod
    def _is_simple_query(text: str) -> bool:
        """Detect simple conversational queries that don't need memory context."""
        t = text.strip().lower().rstrip("?!.")
        # Greetings
        if t in ("hi", "hello", "hey", "hii", "hiii", "yo", "sup", "howdy",
                 "good morning", "good evening", "good night", "thanks",
                 "thank you", "bye", "goodbye", "ok", "okay", "yeah",
                 "yes", "no", "sure", "cool", "nice", "great", "awesome"):
            return True
        # Very short queries (< 5 words) that are just conversation
        words = t.split()
        if len(words) <= 3 and not any(kw in t for kw in ("file", "search", "fetch", "http", "summarize")):
            return True
        return False

    async def run(self, user_input: str, history: list[dict] | None = None) -> str:
        """
        Main entry point. Takes user text, returns agent response string.
        """
        history = history or []

        # ── Step 1: Retrieve memory context ───────────────────
        # Skip memory for simple conversational queries to avoid confusing small models
        if self._is_simple_query(user_input):
            memory_context = ""
        else:
            memory_context = await self.memory.retrieve(user_input)

        # ── Step 2: Route to a tool ───────────────────────────
        tool_name, ctx = await route(user_input)
        logger.info(f"Routed to: {tool_name.value}")

        # ── Step 3: Execute the selected tool ─────────────────
        try:
            response = await self._execute_tool(tool_name, ctx, memory_context, history)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            # Fallback: send to LLM with error context
            response = await self._llm_fallback(user_input, memory_context, history, error=str(e))

        # ── Step 4: Store in memory ───────────────────────────
        await self.memory.store(user_input, response)

        return response

    # ─── Tool dispatch ──────────────────────────────────────────
    async def _execute_tool(
        self,
        tool: ToolName,
        ctx: dict,
        memory_ctx: str,
        history: list[dict],
    ) -> str:

        if tool == ToolName.PARSE_FILE:
            filepath = ctx.get("filepath")
            if not filepath:
                return "⚠️ No file path provided. Use: /file <path>"
            text = parse_file(Path(filepath))
            # After parsing, send to LLM for analysis
            prompt = self._build_prompt(
                ctx.get("prompt", "Analyze this file content."),
                memory_ctx,
                file_content=text,
            )
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

        elif tool == ToolName.OCR_IMAGE:
            filepath = ctx.get("filepath")
            if filepath:
                text = parse_file(Path(filepath))  # unified parser handles images
                prompt = self._build_prompt(
                    ctx.get("prompt", "What does this image contain?"),
                    memory_ctx,
                    file_content=text,
                )
                return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)
            return "⚠️ No image file provided. Use: /file <path_to_image>"

        elif tool == ToolName.SUMMARIZE:
            prompt = self._build_prompt(ctx["prompt"], memory_ctx)
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

        elif tool == ToolName.RUN_COMMAND:
            return await run_sandboxed_command(ctx["prompt"], self.llm)

        elif tool == ToolName.WEB_SEARCH:
            search_results = await web_search(ctx.get("query", ctx["prompt"]))
            prompt = self._build_prompt(
                ctx["prompt"],
                memory_ctx,
                web_results=search_results,
            )
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

        elif tool == ToolName.WEB_FETCH:
            url = ctx.get("url")
            if not url:
                return "⚠️ No URL found. Include a full URL (https://...) in your message."
            page_text = await web_fetch(url)
            prompt = self._build_prompt(
                ctx["prompt"],
                memory_ctx,
                web_content=page_text,
            )
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

        else:  # GENERAL
            offline_warning = ctx.get("offline_warning", "")
            prompt = self._build_prompt(ctx["prompt"], memory_ctx)
            if offline_warning:
                prompt = f"[NOTE: {offline_warning}]\n\n" + prompt
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

    # ─── Prompt construction ────────────────────────────────────
    @staticmethod
    def _build_prompt(
        user_query: str,
        memory_ctx: str = "",
        file_content: str = "",
        web_results: str = "",
        web_content: str = "",
    ) -> str:
        """
        Assembles the full prompt with all available context.
        Context sections are clearly labeled so the LLM knows what's what.
        """
        parts: list[str] = []

        if memory_ctx:
            parts.append(f"[PAST MEMORY CONTEXT]\n{memory_ctx}\n[END MEMORY]")

        if file_content:
            # Truncate very large files to avoid blowing the context window
            truncated = file_content[:8000]
            if len(file_content) > 8000:
                truncated += "\n... [content truncated for context limit]"
            parts.append(f"[FILE CONTENT]\n{truncated}\n[END FILE]")

        if web_results:
            parts.append(f"[WEB SEARCH RESULTS]\n{web_results}\n[END SEARCH]")

        if web_content:
            truncated = web_content[:6000]
            if len(web_content) > 6000:
                truncated += "\n... [page content truncated]"
            parts.append(f"[WEB PAGE CONTENT]\n{truncated}\n[END PAGE]")

        parts.append(f"[USER QUERY]\n{user_query}")

        return "\n\n".join(parts)

    # ─── Fallback ───────────────────────────────────────────────
    async def _llm_fallback(self, user_input: str, memory_ctx: str, history: list[dict] | None = None, error: str = "") -> str:
        prompt = (
            f"[ERROR in tool execution: {error}]\n\n"
            f"Please answer the user's question as best you can.\n\n"
            f"{user_input}"
        )
        if memory_ctx:
            prompt = f"[MEMORY]\n{memory_ctx}\n[END MEMORY]\n\n" + prompt
        return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

    # ─── Utility ────────────────────────────────────────────────
    def print_tools(self):
        print("\n  📦 Available Tools:")
        print("  ─────────────────────────────────────────────")
        print("  📄 parse_file     → Parse TXT, PDF, DOCX files")
        print("  🖼️  ocr_image     → Extract text from images (OCR)")
        print("  📝 summarize      → Summarize or analyze text")
        print("  💬 general        → General Q&A via local LLM")
        print("  🔧 run_command    → Execute sandboxed shell commands")
        print("  🌐 web_search     → Search the web (requires internet)")
        print("  🔗 web_fetch      → Fetch and read a webpage (requires internet)")
        print("  ─────────────────────────────────────────────\n")
