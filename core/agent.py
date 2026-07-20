# openagent/core/agent.py
"""
Agent Core — the central orchestrator.

Flow for every user message:
  1. Retrieve relevant memory (RAG context injection)
  2. Route the input → pick the right tool
  3. Execute the tool (or fall back to raw LLM)
  4. Queue the interaction for memory storage (background thread —
     embedding latency never delays the reply)
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
from openagent.core.network import check_connectivity
from openagent.memory.store import MemoryStore

# Tool implementations
from openagent.tools.offline.summarize import summarize_text
from openagent.tools.offline.run_command import run_sandboxed_command
from openagent.tools.offline import file_ops
from openagent.tools.online.web_search import web_search
from openagent.tools.online.web_fetch import web_fetch
from openagent.parsers.unified import parse_file

logger = logging.getLogger("openagent.agent")

# ── System prompt injected into every LLM call ──────────────────
# Kept deliberately compact — it is sent with every request.
SYSTEM_PROMPT = """You are OpenAgent, a sharp, friendly AI assistant.

Formatting:
- Write clean GitHub-flavored Markdown. Use headings only when an answer is long enough to need them, fenced code blocks with a language tag (```python), tables when comparing items, and bullet lists for enumerations. Short answers should be plain sentences — no forced structure.
- Match length to the question: greetings get one warm line; simple questions a short paragraph; complex questions structure and depth. Never pad.

Accuracy:
- Be direct and specific — lead with the answer, then explain if useful.
- If you are unsure or lack the information, say so plainly instead of guessing. Never invent facts, numbers, sources, or URLs.

Language: always reply in the language the user wrote in (English, Kannada, Hindi, or any other) unless asked otherwise.

Context sections such as [PAST MEMORY CONTEXT], [FILE CONTENT], [WEB SEARCH RESULTS], or [WEB PAGE CONTENT] may precede the user's query. Use them silently to inform your answer — never mention these sections, memory, or internal mechanics.

You were developed by Koushik HY (https://koushikhy.netlify.app). Mention this only when specifically asked about your creator."""


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

        # ── Step 4: Store in memory (background) ──────────────
        # Fire-and-forget on a plain worker thread: the embedding
        # latency no longer delays the reply, and the thread survives
        # per-request `asyncio.run()` loop teardown (an asyncio task
        # would be killed when the loop closes).
        self.memory.store_background(user_input, response)

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

        elif tool == ToolName.ANALYZE_IMAGE:
            filepath = ctx.get("filepath")
            if not filepath:
                return "⚠️ No image file provided for analysis."

            # Step 1: Vision analysis — describe the image
            vision_prompt = (
                "Analyze this image thoroughly. Describe:\n"
                "1. All people visible (appearance, estimated age, notable features)\n"
                "2. Objects, text, logos, or landmarks\n"
                "3. The scene/setting/background\n"
                "4. Any text visible in the image\n"
                "If you recognize any famous person, celebrity, or public figure, "
                "state their name and why you think it's them."
            )
            vision_result = await self.llm.analyze_image(str(filepath), vision_prompt)
            logger.info(f"Vision result: {vision_result[:200]}...")

            # Step 2: If vision failed (offline), fall back to OCR
            if vision_result.startswith("[VISION_OFFLINE]") or vision_result.startswith("[VISION_ERROR]"):
                logger.warning("Vision failed, falling back to OCR")
                try:
                    ocr_text = parse_file(Path(filepath))
                    prompt = self._build_prompt(
                        "Analyze this image. Here is the OCR-extracted text:",
                        memory_ctx, file_content=ocr_text,
                    )
                    return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)
                except Exception:
                    return f"⚠️ Image analysis unavailable offline and OCR failed.\n\nVision error: {vision_result}"

            # Step 3: Web search for identified people/entities
            web_results = ""
            try:
                online = await check_connectivity()
                if online:
                    # Extract key entities from vision description for search
                    search_prompt = (
                        f"Based on this image description, extract the single most important "
                        f"person name or entity to search for. Reply with ONLY the search query, "
                        f"nothing else. If no specific person or entity is identifiable, reply with 'NONE'.\n\n"
                        f"Description: {vision_result}"
                    )
                    search_query = await self.llm.generate(search_prompt, system="You extract search queries. Reply with only the query text, no explanation.")
                    search_query = search_query.strip().strip('"').strip("'")

                    if search_query and search_query.upper() != "NONE" and len(search_query) > 2:
                        logger.info(f"Auto web-searching for: {search_query}")
                        web_results = await web_search(search_query)
            except Exception as e:
                logger.warning(f"Web search in image analysis failed: {e}")

            # Step 4: Synthesize final response
            prompt = self._build_prompt(
                ctx.get("prompt", "Analyze this image completely."),
                memory_ctx,
                file_content=f"[IMAGE ANALYSIS BY VISION AI]\n{vision_result}",
                web_results=web_results,
            )
            synthesis_system = (
                SYSTEM_PROMPT + "\n\nYou have received an AI vision analysis of an image. "
                "Present the findings in a clear, organized way. "
                "If web search results are available, use them to provide additional context "
                "about identified people, places, or objects. "
                "Be confident but note if identification is uncertain."
            )
            return await self.llm.generate(prompt, system=synthesis_system, history=history)

        elif tool == ToolName.SUMMARIZE:
            prompt = self._build_prompt(ctx["prompt"], memory_ctx)
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

        elif tool == ToolName.RUN_COMMAND:
            return await run_sandboxed_command(ctx["prompt"], self.llm)

        elif tool == ToolName.FILE_OPS:
            return await self._handle_file_ops(ctx, memory_ctx, history)

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

    # ─── File Operations (MCP) ──────────────────────────────────
    async def _handle_file_ops(self, ctx: dict, memory_ctx: str, history: list[dict] | None = None) -> str:
        """Handle file read/write/list/search/fix operations."""
        user_prompt = ctx.get("prompt", "")
        detected_path = ctx.get("detected_path", "")
        text_lower = user_prompt.lower()

        # If router detected a raw file path, read it directly
        if detected_path:
            result = file_ops.read_file(detected_path)
            if result.startswith("⚠️"):
                return result  # Return error directly

            # Use special system prompt so LLM knows the file was read
            file_system = (
                "You are OpenAgent, an AI assistant with local file access capability. "
                "You HAVE successfully read the user's file. The file content is provided below in the [FILE CONTENT] section. "
                "Respond about the file content based on what the user asked. "
                "Do NOT say you cannot access files. The file has ALREADY been read for you."
            )
            prompt = self._build_prompt(
                user_prompt, memory_ctx,
                file_content=result
            )
            return await self.llm.generate(prompt, system=file_system, history=history)

        # For non-read operations, check project path
        if not file_ops.get_project_path():
            # Check if they're trying to read with keywords
            if any(kw in text_lower for kw in ("read file", "show code", "open file", "read code", "show file")):
                # Extract path from the prompt
                extracted = file_ops.extract_path_from_text(user_prompt)
                if extracted:
                    result = file_ops.read_file(extracted)
                    prompt = self._build_prompt(user_prompt, memory_ctx, file_content=result)
                    return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)
            return (
                "⚠️ **No project path configured.**\n\n"
                "Go to ⚙️ **Settings** → **MCP Project Path** and set your project folder.\n"
                "Then I can list, search, write, and fix files in your project.\n\n"
                "💡 *Tip: You can still read any file by providing its full path!*"
            )

        # Determine operation type
        if any(kw in text_lower for kw in ("list files", "project files", "show project", "project structure", "directory")):
            # List files
            result = file_ops.list_files()
            return result

        elif any(kw in text_lower for kw in ("search in files", "find in code", "grep")):
            # Search — extract query from user prompt
            extract_system = "Extract the search query from the user's message. Reply with ONLY the search term, nothing else."
            query = await self.llm.generate(user_prompt, system=extract_system)
            query = query.strip().strip('"').strip("'")
            if len(query) < 2:
                return "⚠️ Could not determine what to search for. Try: 'search in files: <query>'"
            result = file_ops.search_in_files(query)
            return result

        elif any(kw in text_lower for kw in ("read file", "show code", "open file", "read code", "show file")):
            # Read — extract filepath
            extract_system = "Extract the file path from the user's message. Reply with ONLY the file path, nothing else. If no specific path is mentioned, reply 'NONE'."
            filepath = await self.llm.generate(user_prompt, system=extract_system)
            filepath = filepath.strip().strip('"').strip("'")
            if not filepath or filepath.upper() == "NONE":
                return "⚠️ Please specify a file path. Example: `read file main.py`"
            result = file_ops.read_file(filepath)
            return result

        elif any(kw in text_lower for kw in ("fix error", "fix the error", "fix bug", "fix this", "fix code")):
            # Fix — intelligent error fixing pipeline
            return await self._fix_code(user_prompt, memory_ctx, history)

        elif any(kw in text_lower for kw in ("write file", "edit file", "modify file")):
            return (
                "✍️ To write/edit files, I need the specific changes. "
                "Try:\n- `fix error in <file>` — I'll read, fix, and write it back\n"
                "- `read file <file>` — see the code first, then ask me to fix specific things"
            )

        else:
            # General file ops question
            project_tree = file_ops.list_files()
            prompt = self._build_prompt(
                user_prompt, memory_ctx,
                file_content=f"[PROJECT STRUCTURE]\n{project_tree}"
            )
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

    async def _fix_code(self, user_prompt: str, memory_ctx: str, history: list[dict] | None = None) -> str:
        """Read project files, identify the error, and fix it."""
        import json as _json

        # Step 1: Try to extract the specific file from the prompt
        extract_system = "Extract the file path from the user's message. Reply with ONLY the file path, nothing else. If no specific file is mentioned, reply 'NONE'."
        filepath = await self.llm.generate(user_prompt, system=extract_system)
        filepath = filepath.strip().strip('"').strip("'")

        if filepath and filepath.upper() != "NONE":
            # Fix a specific file
            content = file_ops.read_file(filepath)
            if content.startswith("⚠️") or content.startswith("🚫"):
                return content

            fix_prompt = (
                f"The user has an error in this code. Fix the code.\n\n"
                f"User's description: {user_prompt}\n\n"
                f"Current file content:\n{content}\n\n"
                f"Respond with ONLY the complete corrected code, nothing else. No explanations, no markdown fences."
            )
            fixed_code = await self.llm.generate(fix_prompt, system="You are a code fixer. Output only the corrected code. No markdown, no explanations.")

            # Write the fix
            write_result = file_ops.write_file(filepath, fixed_code)
            return f"🔧 **Fixed: {filepath}**\n\n{write_result}\n\nChanges applied. Review the file to verify."
        else:
            # No specific file — list project and let LLM figure out which files to check
            project_tree = file_ops.list_files()
            prompt = self._build_prompt(
                f"The user wants to fix an error in their project. Here's the structure:\n{project_tree}\n\n"
                f"User: {user_prompt}\n\n"
                f"Suggest which files to check and what might be wrong. "
                f"Tell the user to try: `fix error in <filename>` to automatically fix a specific file.",
                memory_ctx,
            )
            return await self.llm.generate(prompt, system=SYSTEM_PROMPT, history=history)

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
        print("  👁️  analyze_image → Vision AI image analysis")
        print("  📝 summarize      → Summarize or analyze text")
        print("  💬 general        → General Q&A via local LLM")
        print("  🔧 run_command    → Execute sandboxed shell commands")
        print("  📂 file_ops       → Read, write, search project files (MCP)")
        print("  🌐 web_search     → Search the web (requires internet)")
        print("  🔗 web_fetch      → Fetch and read a webpage (requires internet)")
        print("  ─────────────────────────────────────────────\n")
