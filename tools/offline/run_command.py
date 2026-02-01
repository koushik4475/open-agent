# openagent/tools/offline/run_command.py
"""
Sandboxed Command Execution Tool.

SECURITY MODEL:
  ─────────────────────────────────────────────────
  1. WHITELIST ONLY — only commands in settings.yaml are allowed.
  2. TIMEOUT KILL — any command exceeding max_execution_seconds is killed.
  3. NO SHELL INJECTION — we split args ourselves; no shell=True.
  4. NO ROOT — subprocess inherits current user permissions only.
  ─────────────────────────────────────────────────

The agent first asks the LLM to extract the intended command from the
user's natural language, then validates it against the whitelist before
executing.

Example:
  User: "run command: echo hello world"
  → LLM extracts: ["echo", "hello", "world"]
  → Whitelist check: "echo" is allowed ✅
  → Execute: subprocess.run(["echo", "hello", "world"])
  → Returns: "hello world"
"""

from __future__ import annotations
import subprocess
import shlex
import logging
import json

from openagent.config import settings
from openagent.core.llm import LLMClient

logger = logging.getLogger("openagent.tools.run_command")

EXTRACT_CMD_SYSTEM = """You are a command parser. The user wants to run a shell command.
Extract EXACTLY the command and its arguments from the user's message.
Return ONLY a JSON array of strings. Example: ["echo", "hello", "world"]
Do NOT add explanations. Do NOT add shell operators like |, >, ;, &&.
If no clear command is found, return: ["echo", "No command detected."]"""


async def run_sandboxed_command(user_prompt: str, llm: LLMClient) -> str:
    """
    1. Ask LLM to extract the command from natural language.
    2. Validate against whitelist.
    3. Execute with timeout.
    4. Return stdout or error.
    """
    sandbox_cfg = settings.sandbox

    if not sandbox_cfg.enabled:
        return "⚠️ Sandboxed command execution is disabled in settings.yaml."

    # ── Step 1: Extract command via LLM ─────────────────────
    raw_json = await llm.generate(user_prompt, system=EXTRACT_CMD_SYSTEM)

    try:
        # Strip any markdown code fences the LLM might add
        cleaned = raw_json.strip().strip("`").replace("json", "").strip()
        cmd_parts: list[str] = json.loads(cleaned)
        if not isinstance(cmd_parts, list) or not all(isinstance(x, str) for x in cmd_parts):
            raise ValueError("Expected a JSON array of strings")
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse command from LLM output: {raw_json}")
        return f"⚠️ Could not parse command. LLM returned: {raw_json}"

    if not cmd_parts:
        return "⚠️ Empty command."

    # ── Step 2: Whitelist validation ─────────────────────────
    base_command = cmd_parts[0].lower().strip()

    if base_command not in sandbox_cfg.allowed_commands:
        allowed = ", ".join(sandbox_cfg.allowed_commands)
        return (
            f"🚫 Command '{base_command}' is not allowed.\n"
            f"   Allowed commands: {allowed}\n"
            f"   Edit config/settings.yaml → sandbox.allowed_commands to add more."
        )

    # ── Step 3: Execute with timeout ─────────────────────────
    logger.info(f"Executing sandboxed command: {cmd_parts}")

    try:
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=sandbox_cfg.max_execution_seconds,
            shell=False,                  # CRITICAL: no shell injection
            # Don't run as root; inherits current user
        )

        output = result.stdout.strip()
        errors = result.stderr.strip()

        if result.returncode != 0:
            return f"⚠️ Command exited with code {result.returncode}.\nStderr: {errors}"

        return f"✅ Output:\n{output}" if output else "✅ Command completed (no output)."

    except subprocess.TimeoutExpired:
        return (
            f"⏰ Command timed out after {sandbox_cfg.max_execution_seconds}s. "
            f"Increase sandbox.max_execution_seconds in settings.yaml if needed."
        )
    except FileNotFoundError:
        return f"⚠️ Command '{base_command}' not found on this system."
    except Exception as e:
        logger.error(f"Sandbox execution error: {e}")
        return f"⚠️ Execution error: {e}"
