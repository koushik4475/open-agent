# openagent/core/llm.py
"""
Thin async wrapper around Ollama's local HTTP API.

Ollama exposes a REST endpoint at http://localhost:11434/api/generate
This module is the ONLY place the agent talks to the LLM.
Swapping to a different local runtime (llama.cpp server, etc.)
means editing only this file.
"""

from __future__ import annotations
import json
import logging
import asyncio
import requests

from openagent.config import settings

logger = logging.getLogger("openagent.llm")


class LLMClient:
    """
    Synchronous Ollama client wrapped in an async-friendly executor call.
    We keep the HTTP call synchronous (requests) because Ollama's streaming
    is line-delimited JSON and requests handles that cleanly.
    """

    def __init__(self):
        self.cfg = settings.llm
        self.provider = getattr(self.cfg, "provider", "ollama")
        
        # OpenRouter / DeepSeek Configuration
        if self.provider in ["deepseek", "openrouter"]:
            self.base_url = getattr(self.cfg, "base_url", "https://openrouter.ai/api/v1")
            self.api_key = getattr(self.cfg, "api_key", "")
            # Use 'cloud_model' if available, else fall back to 'model'
            self.model = getattr(self.cfg, "cloud_model", self.cfg.model)
        else:
            self.base_url = self.cfg.host.rstrip("/")
            self.model = self.cfg.model

    async def generate(self, prompt: str, system: str | None = None) -> str:
        """
        Send a prompt, get a response string back.
        Runs the blocking HTTP call in a thread pool so we don't freeze
        the async event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._do_generate, prompt, system
        )

    def _do_generate(self, prompt: str, system: str | None) -> str:
        """blocking HTTP call to LLM provider (Ollama or Cloud)."""
        
        # Try primary provider first
        if self.provider in ["deepseek", "openrouter"]:
            try:
                return self._call_cloud_openai(prompt, system)
            except Exception as e:
                logger.error(f"Cloud provider ({self.provider}) failed: {e}")
                logger.warning("🔄 FALLING BACK to local Ollama...")
                return self._call_ollama(prompt, system)
        else:
            return self._call_ollama(prompt, system)

    def _call_cloud_openai(self, prompt: str, system: str | None) -> str:
        """Call OpenRouter/DeepSeek API (OpenAI compatible)."""
        # Ensure base_url doesn't end with slash, then add endpoint
        # BUT OpenRouter base needs to end with /api/v1 typically
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
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

        resp = requests.post(
            url, json=payload, headers=headers, timeout=self.cfg.timeout_seconds
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Handle different response structures if needed, but usually standard
        try:
            return data["choices"][0]["message"]["content"].strip()
        except KeyError:
            logger.error(f"Unexpected response format: {data}")
            raise ValueError(f"Invalid API response: {data}")

    def _call_ollama(self, prompt: str, system: str | None) -> str:
        """Blocking HTTP POST to Ollama (Local Fallback)."""
        # Always use the local host/model for fallback
        local_host = getattr(self.cfg, "host", "http://localhost:11434")
        local_model = getattr(self.cfg, "model", "phi3:mini") # The local one, not cloud one
        
        url = f"{local_host}/api/generate"
        
        payload: dict = {
            "model": local_model,
            "prompt": prompt,
            "options": {
                "temperature": self.cfg.temperature,
                "num_predict": self.cfg.max_tokens,
            },
            "stream": False,
        }
        if system:
            payload["system"] = system

        logger.info(f"Ollama call → model={local_model}, prompt_len={len(prompt)}")

        try:
            resp = requests.post(
                url, json=payload, timeout=self.cfg.timeout_seconds
            )
            resp.raise_for_status()
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

    def is_available(self) -> bool:
        """Quick health-check."""
        try:
            if self.provider in ["deepseek", "openrouter"]:
                # OpenRouter check uses "GET /models" or similar
                # Just check root or a known endpoint
                url = self.base_url.rstrip("/") + "/models"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                resp = requests.get(url, headers=headers, timeout=5)
                return resp.status_code == 200
            else:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
                return resp.status_code == 200
        except Exception:
            return False
