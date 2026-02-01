# openagent/config/__init__.py
"""
Loads settings.yaml into typed Pydantic models.
Import anywhere: from openagent.config import settings
"""

from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel
import yaml

_CONFIG_PATH = Path(__file__).parent / "settings.yaml"


class LLMConfig(BaseModel):
    provider: str = "ollama"  # Default to ollama
    host: str = "http://localhost:11434"
    base_url: str = "http://localhost:11434"
    api_key: str = ""
    cloud_model: str = "deepseek/deepseek-r1:free"
    model: str
    timeout_seconds: int
    max_tokens: int
    temperature: float


class OCRConfig(BaseModel):
    language: str
    psm: int


class MemoryConfig(BaseModel):
    db_path: str
    collection_name: str
    embedding_model: str
    max_context_chunks: int


class SearchConfig(BaseModel):
    max_results: int
    region: str
    safesearch: str
    timeout_seconds: int


class SandboxConfig(BaseModel):
    enabled: bool
    allowed_commands: list[str]
    max_execution_seconds: int


class NetworkConfig(BaseModel):
    check_host: str
    check_port: int
    check_timeout_seconds: int


class LoggingConfig(BaseModel):
    level: str
    file: str


class Settings(BaseModel):
    llm: LLMConfig
    ocr: OCRConfig
    memory: MemoryConfig
    search: SearchConfig
    sandbox: SandboxConfig
    network: NetworkConfig
    logging: LoggingConfig


def _load() -> Settings:
    with open(_CONFIG_PATH, "r") as f:
        raw = yaml.safe_load(f)
    return Settings(**raw)


settings: Settings = _load()
