# openagent/config/cli.py
"""
Interactive CLI REPL for OpenAgent.

Commands:
  <text>            → Send to the agent for processing
  /help             → Show this help
  /tools            → List available tools
  /status           → Show system status (LLM, network, memory)
  /clear            → Clear conversation history
  /file <path>      → Parse a file and feed its content to the agent
  /quit or /exit    → Exit
"""

from __future__ import annotations
import sys
import asyncio
from pathlib import Path

# Adjust import path so this works both as module and script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from openagent.core.agent import Agent
from openagent.core.network import check_connectivity


BANNER = """
╔══════════════════════════════════════════════════════════╗
║              🤖  OpenAgent — Offline-First AI            ║
║         Zero-cost · Open-source · Hybrid (on/offline)    ║
╠══════════════════════════════════════════════════════════╣
║  Type /help for commands.  Type /status to check setup.  ║
╚══════════════════════════════════════════════════════════╝
"""


async def main():
    print(BANNER)
    agent = await Agent.create()
    history: list[dict] = []  # Running conversation context

    while True:
        try:
            raw = input("\n🧑 You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye.")
            break

        if not raw:
            continue

        # ── slash commands ────────────────────────────────────
        if raw.startswith("/"):
            cmd = raw.lower().split()[0]

            if cmd in ("/quit", "/exit"):
                print("👋 Goodbye.")
                break

            elif cmd == "/help":
                print(__doc__)
                continue

            elif cmd == "/tools":
                agent.print_tools()
                continue

            elif cmd == "/status":
                online = await check_connectivity()
                print(f"  LLM model : {agent.cfg.llm.model}")
                print(f"  LLM host  : {agent.cfg.llm.host}")
                print(f"  Network   : {'🟢 Online' if online else '🔴 Offline'}")
                print(f"  Memory    : {agent.cfg.memory.db_path}")
                continue

            elif cmd == "/clear":
                history.clear()
                print("  ✅ Conversation history cleared.")
                continue

            elif cmd == "/file":
                parts = raw.split(None, 1)
                if len(parts) < 2:
                    print("  ⚠️  Usage: /file <path>")
                    continue
                filepath = Path(parts[1].strip().strip("'\""))
                if not filepath.exists():
                    print(f"  ⚠️  File not found: {filepath}")
                    continue
                # Feed the file path as context in the next message
                raw = f"[FILE:{filepath}] Please parse and analyze this file."
                # Fall through to agent processing below

            else:
                print(f"  ⚠️  Unknown command: {cmd}. Type /help.")
                continue

        # ── send to agent ─────────────────────────────────────
        print("\n🤖 Agent> ", end="", flush=True)
        response = await agent.run(raw, history)
        print(response)

        # Store in local history (trimmed to last 20 turns)
        history.append({"role": "user", "content": raw})
        history.append({"role": "assistant", "content": response})
        if len(history) > 40:
            history = history[-40:]


def run():
    """Entry point called from __main__.py"""
    asyncio.run(main())
