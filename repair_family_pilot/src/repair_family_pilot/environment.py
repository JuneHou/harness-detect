"""Model-service and case-environment checks.

A missing local binary is not the check. The configured service must answer
and list the model. Failure is environment_blocked, not a scientific finding.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


def model_id_from_source(source: str) -> str:
    match = re.search(r"""MODEL\s*=\s*['"]([^'"]+)['"]""", source)
    if match:
        return match.group(1)
    match = re.search(r"""model_name\s*=\s*['"]([^'"]+)['"]""", source)
    if match:
        return match.group(1)
    match = re.search(r"""model\s*=\s*['"]([^'"]+)['"]""", source)
    if match:
        return match.group(1)
    return ""


def provider_from_source(source: str) -> str:
    if "ollama" in source:
        return "ollama"
    if "openai" in source or "ChatOpenAI" in source or "langchain_openai" in source:
        return "openai"
    return "undefined"


def probe_accepts(status_code: int, body: str, model_id: str) -> bool:
    return status_code == 200 and bool(model_id) and model_id in body


def check_model(source: str, timeout: int = 10) -> dict:
    provider = provider_from_source(source)
    model_id = model_id_from_source(source)
    if provider == "undefined":
        return {"status": "environment_blocked", "finding": "provider_check_undefined", "model_id": model_id}
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        return {"status": "environment_blocked", "finding": "missing_api_key", "model_id": model_id}
    if provider == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        url = host + "/api/tags"
        headers = {}
    else:
        host = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        url = host + "/models"
        headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            code = response.status
    except Exception as exc:
        return {"status": "environment_blocked", "finding": f"service_unreachable:{exc.__class__.__name__}", "model_id": model_id}
    if not probe_accepts(code, body, model_id):
        return {"status": "environment_blocked", "finding": "model_unavailable", "model_id": model_id}
    return {"status": "ok", "finding": "", "model_id": model_id}


HARNESSFIX_PYTHON = Path("/data/wang/junh/envs/harnessfix/bin/python")


def ensure_case_env(root: Path, case_id: str, requirements: str) -> dict:
    """Run every case with the HarnessFix environment. Do not create another env."""
    del root, case_id
    python = HARNESSFIX_PYTHON
    if not python.exists():
        return {"status": "environment_blocked", "finding": "harnessfix_missing", "python": ""}
    if requirements.strip():
        check = subprocess.run(
            [str(python), "-c", "from langchain_openai import ChatOpenAI; from langchain.agents import initialize_agent, load_tools; from langchain.memory import ConversationBufferMemory"],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            pip = python.parent / "pip"
            requirement_file = Path("/tmp/harnessfix-case-requirements.txt")
            requirement_file.write_text(requirements, encoding="utf-8")
            installed = subprocess.run([str(pip), "install", "-r", str(requirement_file)], capture_output=True, text=True)
            if installed.returncode != 0:
                return {"status": "environment_blocked", "finding": "case_install_failed", "python": str(python)}
    return {"status": "ok", "finding": "", "python": str(python)}


def source_parses(source: str) -> bool:
    try:
        ast.parse(source)
    except SyntaxError:
        return False
    return True
