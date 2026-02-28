# openagent/tools/offline/file_ops.py
"""
MCP-like File Operations Tool.

Allows the agent to read, write, list, and search files.

READ:   Any absolute path the user provides can be read.
WRITE:  Restricted to configured project_path only.
LIST:   Project path only.
SEARCH: Project path only.
"""

from __future__ import annotations
import os
import logging
import re
from pathlib import Path

logger = logging.getLogger("openagent.tools.file_ops")

MAX_READ_SIZE = 36_700_160   # ~35MB max per file read
MAX_LIST_DEPTH = 3
MAX_LIST_FILES = 100

_project_path: str = ""


def set_project_path(path: str):
    """Set the project path (called from server.py when settings are updated)."""
    global _project_path
    _project_path = path.strip()
    logger.info(f"MCP project path set to: {_project_path}")


def get_project_path() -> str:
    return _project_path


def extract_path_from_text(text: str) -> str | None:
    """Try to extract a file path from user text."""
    # Match Windows absolute paths like C:\path\to\file.ext
    win_match = re.search(r'([A-Za-z]:\\[^\s\'"<>|]+)', text)
    if win_match:
        return win_match.group(1).strip()

    # Match Unix absolute paths like /home/user/file.ext
    unix_match = re.search(r'(/[^\s\'"<>|]+)', text)
    if unix_match:
        return unix_match.group(1).strip()

    return None


def read_file(filepath: str) -> str:
    """Read a file's contents. Accepts any absolute path."""
    path = Path(filepath).resolve()

    if not path.exists():
        return f"⚠️ File not found: {path}"
    if not path.is_file():
        return f"⚠️ Not a file: {path}"

    size = path.stat().st_size
    if size > MAX_READ_SIZE:
        return f"⚠️ File too large ({size:,} bytes). Max is {MAX_READ_SIZE:,} bytes."

    # For binary files like PDFs, use the parser
    if path.suffix.lower() in ('.pdf', '.docx', '.doc'):
        try:
            from openagent.parsers.unified import parse_file
            content = parse_file(path)
            return f"📄 **{path.name}** ({len(content)} chars)\n\n{content}"
        except Exception as e:
            return f"⚠️ Error parsing {path.name}: {e}"

    # For images, note this
    if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff'):
        return f"🖼️ **{path.name}** is an image file. Use `analyze this image:` or drag & drop it for vision analysis."

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        lang = _guess_lang(path)
        if lang:
            return f"📄 **{path.name}** ({len(content)} chars)\n\n```{lang}\n{content}\n```"
        else:
            return f"📄 **{path.name}** ({len(content)} chars)\n\n{content}"
    except Exception as e:
        return f"⚠️ Error reading file: {e}"


def _validate_project_path(filepath: str) -> tuple[bool, str, Path]:
    """Validate path is within project directory (for write ops)."""
    if not _project_path:
        return False, "⚠️ No project path configured. Set it in ⚙️ Settings → MCP Project Path.", Path()

    project = Path(_project_path).resolve()
    if not project.exists():
        return False, f"⚠️ Project path does not exist: {_project_path}", Path()

    target = Path(filepath)
    if not target.is_absolute():
        target = project / filepath
    target = target.resolve()

    try:
        target.relative_to(project)
    except ValueError:
        return False, f"🚫 Write access denied. Path is outside project directory.\n  Project: {project}\n  Requested: {target}", Path()

    return True, "", target


def write_file(filepath: str, content: str) -> str:
    """Write content to a file. Restricted to project path."""
    valid, err, path = _validate_project_path(filepath)
    if not valid:
        return err

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✅ File written: {path} ({len(content)} chars)"
    except Exception as e:
        return f"⚠️ Error writing file: {e}"


def list_files(directory: str = "") -> str:
    """List files in the project directory (or subdirectory)."""
    if not _project_path:
        return "⚠️ No project path configured. Set it in ⚙️ Settings → MCP Project Path."

    project = Path(_project_path).resolve()
    target = project if not directory else (project / directory).resolve()

    try:
        target.relative_to(project)
    except ValueError:
        return "🚫 Access denied. Path outside project."

    if not target.exists():
        return f"⚠️ Directory not found: {target}"

    result = [f"📂 **{target.name or target}/**\n"]
    count = 0

    def walk(p: Path, depth: int, prefix: str):
        nonlocal count
        if depth > MAX_LIST_DEPTH or count > MAX_LIST_FILES:
            return
        try:
            entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        for entry in entries:
            if entry.name.startswith('.') or entry.name in ('__pycache__', 'node_modules', '.git', 'venv', '.venv'):
                continue
            count += 1
            if count > MAX_LIST_FILES:
                result.append(f"{prefix}... and more files\n")
                return
            if entry.is_dir():
                result.append(f"{prefix}📁 {entry.name}/\n")
                walk(entry, depth + 1, prefix + "  ")
            else:
                size = entry.stat().st_size
                result.append(f"{prefix}📄 {entry.name} ({_human_size(size)})\n")

    walk(target, 0, "  ")
    return "".join(result)


def search_in_files(query: str, directory: str = "", extensions: list[str] = None) -> str:
    """Search for a string/pattern within project files."""
    if not _project_path:
        return "⚠️ No project path configured."

    project = Path(_project_path).resolve()
    target = project if not directory else (project / directory).resolve()

    try:
        target.relative_to(project)
    except ValueError:
        return "🚫 Access denied."

    if not target.exists():
        return f"⚠️ Directory not found: {target}"

    if not extensions:
        extensions = ['.py', '.js', '.ts', '.html', '.css', '.yaml', '.yml', '.json', '.txt', '.md', '.java', '.cpp', '.c', '.h']

    results = []
    file_count = 0

    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', 'venv', '.venv')]
        for fname in files:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = Path(root) / fname
            file_count += 1
            if file_count > 200:
                break
            try:
                content = fpath.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()
                for i, line in enumerate(lines, 1):
                    if query.lower() in line.lower():
                        rel = fpath.relative_to(project)
                        results.append(f"  `{rel}` line {i}: `{line.strip()[:120]}`")
                        if len(results) > 30:
                            results.append("  ... (more results truncated)")
                            return f"🔍 Search results for '{query}':\n\n" + "\n".join(results)
            except Exception:
                continue

    if not results:
        return f"🔍 No results found for '{query}' in {target}"

    return f"🔍 Search results for '{query}':\n\n" + "\n".join(results)


def _guess_lang(p: Path) -> str:
    ext_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.html': 'html',
               '.css': 'css', '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json',
               '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.md': 'markdown', '.sh': 'bash'}
    return ext_map.get(p.suffix.lower(), '')


def _human_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.0f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"
