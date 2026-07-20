# openagent/core/llm.py
"""
Thin async wrapper around the LLM providers.

Talks to a cloud OpenAI-compatible API (Groq / OpenRouter / DeepSeek)
with automatic fallback to local Ollama (http://localhost:11434).
This module is the ONLY place the agent talks to the LLM, so swapping
providers means editing only this file.

Performance notes:
  - All HTTP goes through one shared requests.Session (keep-alive +
    connection pooling — saves a TLS handshake per call).
  - The pre-flight connectivity probe is TTL-cached (~30 s) instead of
    opening a raw socket before every generate/stream call.
"""

from __future__ import annotations
import json
import logging
import asyncio
import base64
import socket
import os
import threading
import time
import requests

from openagent.config import settings

# This reads your key from HuggingFace Secrets (environment variable)
# Falls back to settings.yaml if not found
_api_key_from_env = os.environ.get("GROQ_API_KEY", "")
if _api_key_from_env:
    settings.llm.api_key = _api_key_from_env

logger = logging.getLogger("openagent.llm")

# ── Shared HTTP session (connection pooling) ────────────────────
# One pooled requests.Session for every HTTP call in this module
# (cloud chat, streaming, vision, Ollama, health checks). Reusing
# the session keeps TCP/TLS connections alive between calls, which
# saves a full TLS handshake per request against the same host.
# requests.Session is safe for concurrent use across threads.
_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=8)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

# ── Connectivity check with TTL cache ───────────────────────────
# This used to open a raw socket before EVERY generate/stream call.
# Cache the result (success AND failure) for a short window on a
# monotonic clock so bursts of requests pay for a single probe.
_NET_CHECK_TTL_SECONDS = 30.0
_net_check_lock = threading.Lock()
_net_check_cached: bool | None = None
_net_check_at: float = 0.0


def _quick_net_check(force: bool = False) -> bool:
    """Fast connectivity check (2 second timeout), cached ~30 seconds.

    Pass force=True to bypass the cache and probe immediately.
    """
    global _net_check_cached, _net_check_at
    with _net_check_lock:
        if (
            not force
            and _net_check_cached is not None
            and time.monotonic() - _net_check_at < _NET_CHECK_TTL_SECONDS
        ):
            return _net_check_cached
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(("1.1.1.1", 443))
        sock.close()
        result = True
    except Exception:
        result = False
    with _net_check_lock:
        _net_check_cached = result
        _net_check_at = time.monotonic()
    return result


class LLMClient:
    """
    Synchronous Ollama client wrapped in an async-friendly executor call.
    We keep the HTTP call synchronous (requests) because Ollama's streaming
    is line-delimited JSON and requests handles that cleanly.
    """

    # How much conversation history we replay to the model.
    HISTORY_MAX_MESSAGES = 20   # 20 messages ≈ 10 user/assistant turns
    HISTORY_MAX_CHARS = 4000    # per-message cap so one huge answer can't blow the context

    @classmethod
    def _history_messages(cls, history: list[dict] | None) -> list[dict]:
        """Normalize recent conversation turns into OpenAI-style messages.

        Shared by the cloud (messages array) and Ollama (inline text)
        paths so both providers see the same multi-turn context.
        """
        messages: list[dict] = []
        if not history:
            return messages
        for msg in history[-cls.HISTORY_MAX_MESSAGES:]:
            role = msg.get("role", "user")
            content = (msg.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content[:cls.HISTORY_MAX_CHARS]})
        return messages

    def __init__(self):
        self.cfg = settings.llm
        self.provider = getattr(self.cfg, "provider", "ollama")
        # OpenRouter / DeepSeek Configuration
        if self.provider in ["deepseek", "openrouter", "groq"]:
            self.base_url = getattr(self.cfg, "base_url", "https://openrouter.ai/api/v1")
            
            # Security: Prioritize environment variable over config file
            env_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
            self.api_key = env_key or getattr(self.cfg, "api_key", "")
            
            # Use 'cloud_model' if available, else fall back to 'model'
            self.model = getattr(self.cfg, "cloud_model", self.cfg.model)
        else:
            self.base_url = self.cfg.host.rstrip("/")
            self.model = self.cfg.model

    async def generate(self, prompt: str, system: str | None = None, history: list[dict] | None = None) -> str:
        """
        Send a prompt, get a response string back.
        Runs the blocking HTTP call in a thread pool so we don't freeze
        the async event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._do_generate, prompt, system, history
        )

    async def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """
        Send an image to Groq's vision model for analysis.
        Returns a description of the image contents (people, objects, scene, text).
        """
        import os
        if not os.path.exists(image_path):
            return f"⚠️ Image file not found: {image_path}"

        # Read and base64-encode the image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Detect MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".bmp": "image/bmp", ".tiff": "image/tiff", ".gif": "image/gif"}
        mime_type = mime_map.get(ext, "image/jpeg")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._call_vision_api, image_data, mime_type, prompt
        )

    def _call_vision_api(self, image_base64: str, mime_type: str, prompt: str) -> str:
        """Blocking call to Groq's vision-capable model."""
        if not _quick_net_check():
            return "[VISION_OFFLINE] No internet — cannot analyze image with vision model."

        # Groq decommissioned llama-3.2-*-vision-preview; qwen3.6-27b is the
        # current multimodal model (see console.groq.com/docs/vision).
        vision_model = getattr(self.cfg, "vision_model", "qwen/qwen3.6-27b")
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:{mime_type};base64,{image_base64}"
                }}
            ]}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": vision_model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 1024,
        }

        logger.info(f"Vision API call → model={vision_model}")

        try:
            resp = _session.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return f"[VISION_ERROR] Vision analysis failed: {e}"

    def _do_generate(self, prompt: str, system: str | None, history: list[dict] | None = None) -> str:
        """blocking HTTP call to LLM provider (Ollama or Cloud)."""
        
        if self.provider in ["deepseek", "openrouter", "groq"]:
            # Quick connectivity check — skip cloud if offline (avoids 60s timeout)
            if not _quick_net_check():
                logger.warning("📡 No internet detected — using local Ollama directly")
                return self._call_ollama(prompt, system, history)
            try:
                return self._call_cloud_openai(prompt, system, history)
            except Exception as e:
                logger.error(f"Cloud provider ({self.provider}) failed: {e}")
                logger.warning("🔄 FALLING BACK to local Ollama...")
                return self._call_ollama(prompt, system, history)
        else:
            return self._call_ollama(prompt, system, history)

    def _call_cloud_openai(self, prompt: str, system: str | None, history: list[dict] | None = None) -> str:
        """Call Groq/OpenRouter/DeepSeek API (OpenAI compatible)."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        # Include recent conversation turns as real role messages
        messages.extend(self._history_messages(history))

        messages.append({"role": "user", "content": prompt})

        # Ensure we send the headers for OpenRouter
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000", # Optional for OpenRouter
            "X-Title": "OpenAgent",                  # Optional for OpenRouter
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": False
        }
        
        logger.info(f"Cloud call ({self.provider}) → model={self.model}, prompt_len={len(prompt)}")

        resp = _session.post(
            url, json=payload, headers=headers, timeout=self.cfg.timeout_seconds
        )
        resp.raise_for_status()
        resp.encoding = "utf-8"
        data = resp.json()

        # Handle different response structures if needed, but usually standard
        try:
            return data["choices"][0]["message"]["content"].strip()
        except KeyError:
            logger.error(f"Unexpected response format: {data}")
            raise ValueError(f"Invalid API response: {data}")

    def _call_ollama(self, prompt: str, system: str | None, history: list[dict] | None = None) -> str:
        """Blocking HTTP POST to Ollama (Local Fallback)."""
        # Always use the local host/model for fallback
        local_host = getattr(self.cfg, "host", "http://localhost:11434")
        local_model = getattr(self.cfg, "model", "phi3:mini")

        # Use a simpler system prompt for local models — they get confused by complex ones
        simple_system = (
            "You are OpenAgent, a helpful AI assistant. "
            "Answer the user's question directly and concisely. "
            "Do not make up conversations or reference past context unless asked. "
            "For greetings, just greet back briefly."
        )

        # /api/generate has no messages array, so replay a few recent
        # turns as labelled text ahead of the prompt. Kept short (last
        # 10 messages, tighter per-message cap) — small local models
        # have small context windows and slow prompt ingestion.
        recent = self._history_messages(history)[-10:]
        if recent:
            convo = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:1500]}"
                for m in recent
            )
            prompt = f"[RECENT CONVERSATION]\n{convo}\n[END CONVERSATION]\n\n{prompt}"

        url = f"{local_host}/api/generate"

        payload: dict = {
            "model": local_model,
            "prompt": prompt,
            "options": {
                "temperature": 0.5,  # Lower temperature for more focused responses
                "num_predict": 512,  # Cap output length to prevent rambling
            },
            "stream": False,
        }
        payload["system"] = simple_system

        logger.info(f"Ollama call → model={local_model}, prompt_len={len(prompt)}")

        try:
            resp = _session.post(
                url, json=payload, timeout=self.cfg.timeout_seconds
            )
            resp.raise_for_status()
            resp.encoding = "utf-8"
            data = resp.json()
            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            logger.error("Ollama is not running. Start it with: ollama serve")
            return (
                "⚠️  ERROR: Cannot connect to Ollama. "
                "Make sure Ollama is running (ollama serve) and the model is pulled "
                f"(ollama pull {self.cfg.model})."
            )
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM HTTP error: {e}")
            if e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return f"⚠️  ERROR: LLM returned failure: {e}"
        except requests.exceptions.Timeout:
            logger.error("LLM call timed out")
            return "⚠️  ERROR: LLM response timed out. Try a shorter prompt or increase timeout in settings.yaml."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"⚠️  ERROR: {e}"

    def stream_generate(self, prompt: str, system: str | None = None, history: list[dict] | None = None):
        """
        Streaming version of generate — yields tokens one at a time.
        Used for SSE streaming to the browser for instant feel.
        Falls back to non-streaming Ollama if cloud fails.
        """
        if self.provider in ["deepseek", "openrouter", "groq"]:
            if not _quick_net_check():
                logger.warning("📡 No internet — falling back to Ollama (non-streaming)")
                yield self._call_ollama(prompt, system, history)
                return
            try:
                yield from self._stream_cloud_openai(prompt, system, history)
                return
            except Exception as e:
                logger.error(f"Cloud streaming failed: {e}")
                logger.warning("🔄 FALLING BACK to local Ollama (non-streaming)...")
                yield self._call_ollama(prompt, system, history)
                return
        else:
            yield self._call_ollama(prompt, system, history)

    def _stream_cloud_openai(self, prompt: str, system: str | None, history: list[dict] | None = None):
        """Streaming call to Groq/OpenRouter — yields tokens as they arrive."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        messages.extend(self._history_messages(history))

        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "OpenAgent",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": True
        }

        logger.info(f"Cloud STREAM ({self.provider}) → model={self.model}")

        resp = _session.post(
            url, json=payload, headers=headers,
            timeout=self.cfg.timeout_seconds, stream=True
        )
        resp.raise_for_status()
        resp.encoding = "utf-8"

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def is_available(self) -> bool:
        """Quick health-check."""
        try:
            if self.provider in ["deepseek", "openrouter", "groq"]:
                # OpenRouter check uses "GET /models" or similar
                # Just check root or a known endpoint
                url = self.base_url.rstrip("/") + "/models"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                resp = _session.get(url, headers=headers, timeout=5)
                return resp.status_code == 200
            else:
                resp = _session.get(f"{self.base_url}/api/tags", timeout=3)
                return resp.status_code == 200
        except Exception:
            return False
