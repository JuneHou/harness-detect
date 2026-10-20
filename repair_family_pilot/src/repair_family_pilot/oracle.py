"""Published-test assertion classes and result checks."""

from __future__ import annotations

import ast
import re
from typing import Optional


CONTENT_CALLS = {"assertEqual", "assertAlmostEqual", "assertIn"}
WEAK_CALLS = {"assertIsNotNone", "assertIsInstance", "assertTrue", "assertGreaterEqual"}
CRITERION = re.compile(r"yes or no|expected answer|should return|correct answer|capital of", re.I)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _constant(node: ast.AST):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def inspect_source(test_source: str, readme: str = "") -> dict:
    findings = []
    content = []
    weak = []
    try:
        tree = ast.parse(test_source)
    except SyntaxError:
        return {"oracle_status": "oracle_unavailable", "test_strength": "unparsed", "content_checks": [], "findings": ["test_parse_error"]}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name in CONTENT_CALLS and len(node.args) >= 2:
            expected = _constant(node.args[0] if name == "assertIn" else node.args[1])
            if expected is not None:
                content.append({"kind": name, "expected": expected})
        elif name in WEAK_CALLS:
            weak.append(name)
    concrete = bool(content) or bool(CRITERION.search(test_source) or CRITERION.search(readme))
    if content:
        status = "content"
        strength = "content"
    elif weak and concrete:
        status = "oracle_needs_strengthening"
        strength = "weak"
        findings.append("oracle_needs_strengthening")
    else:
        status = "oracle_unavailable"
        strength = "weak" if weak else "absent"
        findings.append("oracle_unavailable")
    return {
        "oracle_status": status,
        "test_strength": strength,
        "content_checks": content,
        "findings": findings,
    }


def check_result(text: str, checks: list) -> Optional[bool]:
    if not checks:
        return None
    for check in checks:
        expected = check["expected"]
        if check["kind"] == "assertIn":
            if str(expected).lower() not in text.lower():
                return False
        elif check["kind"] == "assertAlmostEqual":
            try:
                if abs(float(text.strip()) - float(expected)) > 1e-6:
                    return False
            except ValueError:
                return False
        else:
            if text.strip() != str(expected):
                return False
    return True
