"""Semantic audit of the pinned SelfHeal AgentDefect archive.

A diff path is stored separately. A repair is recorded only when this module
states its mechanism, scope, exact patch, and why that patch applies alone.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import zipfile
from pathlib import Path

from repair_family_pilot.oracle import inspect_source

ARCHIVE = Path("/data/wang/junh/githubs/SelfHeal/AgentDefect.zip")
EXPECTED_SHA256 = "9063744afae7a2912abf0465d6624d0e266b70239a3c7dd1a4b087f012891e0a"
LEAD_ORDER = ("79149108", "76364591", "76906469")

# Hand-justified repairs. Two hunks are not enough to enter this table.
JUSTIFIED = {
    "76906469": [
        {
            "repair_id": "A",
            "mechanism": "memory representation",
            "scope": "ConversationBufferMemory constructor in run_buggy.py",
            "old": 'memory = ConversationBufferMemory(memory_key="chat_history")',
            "new": 'memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)',
            "why_independent": "This patch changes only the object returned as chat history. It leaves the agent class, the parsing flag, and the pinned model id as they are in the buggy program.",
        },
        {
            "repair_id": "B",
            "mechanism": "agent control and parsing policy",
            "scope": "initialize_agent call and run_agent call site in run_buggy.py",
            "old": """agent_test = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    memory=memory,
    verbose=False
)""",
            "new": """agent_test = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=False,
    memory=memory
)""",
            "why_independent": "This patch changes the agent class and removes the parsing-error handler. It does not edit the memory constructor or the model id. The call name stays agent_test so the patch applies without the memory edit.",
        },
    ]
}


def archive_sha256(path: Path = ARCHIVE) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case_ids(archive: zipfile.ZipFile) -> list:
    ids = set()
    for name in archive.namelist():
        parts = name.split("/")
        if len(parts) >= 2 and parts[0] == "AgentDefect" and parts[1] and not parts[1].startswith(".") and not parts[1].startswith("_"):
            if parts[1] != "":
                ids.add(parts[1])
    return sorted(ids)


def _read(archive: zipfile.ZipFile, case_id: str, filename: str) -> str | None:
    key = f"AgentDefect/{case_id}/{filename}"
    if key not in archive.namelist():
        return None
    return archive.read(key).decode("utf-8", errors="replace")


def _behavior(diff_text: str, case_id: str) -> str:
    lowered = diff_text.lower()
    if case_id == "76364591":
        return "The published fix sets return_direct on the calculator tool, so the tool result is returned to the user without another agent step. That is one setting, not two repairs."
    if case_id == "76906469":
        return "The published fix changes three behaviors at once: it drops the pinned gpt-4 model id, it asks memory to return message objects, and it switches the agent to a conversational class while removing the parsing-error handler. The model-id edit is not a repair in this experiment."
    if case_id == "79149108":
        return "After the model replies, the fixed program appends that assistant message to the stored history. The buggy program keeps the user turn and then invokes the model without storing the assistant reply."
    if "return_messages" in lowered:
        return "The edit changes how conversation memory is returned to the next model call."
    if "return_direct" in lowered:
        return "The edit changes whether a tool result is returned directly to the user."
    if "messages.append" in lowered and "assistant" in lowered:
        return "The edit changes whether the assistant reply is written into the stored conversation."
    if "agenttype" in lowered:
        return "The edit changes which agent class runs the conversation and how that class handles tool or parsing steps."
    if "filter" in lowered and "retriev" in lowered:
        return "The edit changes whether retrieval can be restricted to a named source document."
    if "prompt" in lowered or "template" in lowered:
        return "The edit changes the instruction text the harness sends to the model."
    added = [line[1:].strip() for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:].strip() for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]
    added = [line for line in added if line and not line.startswith("#")]
    removed = [line for line in removed if line and not line.startswith("#")]
    if not added and not removed:
        return "The published pair has no behavioral code change in run_buggy.py versus run_fixed.py."
    return "The published fix replaces {removed} with {added}.".format(
        removed=removed[0][:180] if removed else "nothing",
        added=added[0][:180] if added else "nothing",
    )


def _harness_sentence(diff_text: str, source: str, case_id: str) -> str:
    prefix = ""
    if "langchain" in source or "ollama" in source:
        prefix = "Imports show the file is agent code; they are not the repair. "
    return prefix + _behavior(diff_text, case_id)


def _findings_for_repairs(case_id: str, diff_text: str, repairs: list, oracle_findings: list) -> list:
    findings = list(oracle_findings)
    if case_id == "76364591":
        findings.append("single_setting_do_not_split")
    lowered = diff_text.lower()
    if "model_name" in lowered or "model=" in lowered:
        findings.append("unrelated_model_edit")
    if case_id == "76364591":
        return findings
    if len(repairs) == 2:
        findings.append("two_repairs_documented")
    elif len(repairs) == 1:
        findings.append("only_one_demonstrated_repair")
    else:
        findings.append("two_repairs_not_justified")
    return findings


def audit_case(archive: zipfile.ZipFile, case_id: str, diff_dir: Path) -> dict:
    buggy = _read(archive, case_id, "run_buggy.py")
    fixed = _read(archive, case_id, "run_fixed.py")
    test_src = _read(archive, case_id, "test.py") or ""
    readme = _read(archive, case_id, "readme.md") or ""
    requirements = _read(archive, case_id, "requirements.txt") or ""
    available = [name for name in ("run_buggy.py", "run_fixed.py", "test.py", "readme.md", "requirements.txt") if _read(archive, case_id, name) is not None]
    oracle = inspect_source(test_src, readme)
    if buggy is None or fixed is None:
        findings = ["missing_run_buggy" if buggy is None else "missing_run_fixed"] + oracle["findings"]
        return {
            "case_id": case_id,
            "available_files": ",".join(available),
            "defect_description": "This case has no buggy/fixed program pair to compare.",
            "diff_path": "",
            "changed_mechanisms": "",
            "dependency_runtime": requirements + "\n" + "\n".join(line for line in readme.splitlines() if line.lower().startswith("how to run") or line[:2].rstrip(".").isdigit() or line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.")),
            "harness_relevance": "No program pair is available, so no harness mechanism can be named.",
            "test_strength": oracle["test_strength"],
            "oracle_status": oracle["oracle_status"],
            "proposed_candidates": "[]",
            "findings": json.dumps(findings),
        }
    diff_lines = list(difflib.unified_diff(buggy.splitlines(), fixed.splitlines(), fromfile="run_buggy.py", tofile="run_fixed.py", lineterm=""))
    diff_text = "\n".join(diff_lines) + "\n"
    diff_path = diff_dir / f"{case_id}.diff"
    diff_path.write_text(diff_text, encoding="utf-8")
    repairs = []
    if case_id in JUSTIFIED:
        for item in JUSTIFIED[case_id]:
            if item["old"] not in buggy:
                continue
            repairs.append(item)
    how_to = []
    capture = False
    for line in readme.splitlines():
        if line.strip().lower().startswith("how to run"):
            capture = True
        if capture:
            how_to.append(line)
    findings = _findings_for_repairs(case_id, diff_text, repairs if case_id != "76364591" else [], oracle["findings"])
    if case_id == "76364591":
        repairs = []
    return {
        "case_id": case_id,
        "available_files": ",".join(available),
        "defect_description": _behavior(diff_text, case_id),
        "diff_path": str(diff_path),
        "changed_mechanisms": json.dumps([
            {"repair_id": item["repair_id"], "mechanism": item["mechanism"], "scope": item["scope"]}
            for item in repairs
        ]),
        "dependency_runtime": requirements + ("\n" + "\n".join(how_to) if how_to else ""),
        "harness_relevance": _harness_sentence(diff_text, buggy, case_id),
        "test_strength": oracle["test_strength"],
        "oracle_status": oracle["oracle_status"],
        "proposed_candidates": json.dumps(repairs),
        "findings": json.dumps(findings),
    }


def queue_from_rows(rows: list) -> list:
    eligible = []
    for row in rows:
        findings = json.loads(row["findings"])
        repairs = json.loads(row["proposed_candidates"])
        if "oracle_unavailable" in findings:
            continue
        if len(repairs) != 2:
            continue
        eligible.append(row["case_id"])
    ordered = [case_id for case_id in LEAD_ORDER if case_id in eligible]
    ordered.extend(sorted(case_id for case_id in eligible if case_id not in ordered))
    return ordered


def run_audit(project_root: Path, archive_path: Path = ARCHIVE) -> dict:
    digest = archive_sha256(archive_path)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"archive sha256 {digest} does not match the pinned hash")
    audit_dir = project_root / "artifacts" / "audit"
    diff_dir = audit_dir / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with zipfile.ZipFile(archive_path) as archive:
        for case_id in _case_ids(archive):
            rows.append(audit_case(archive, case_id, diff_dir))
    csv_path = audit_dir / "case_audit.csv"
    columns = [
        "case_id", "available_files", "defect_description", "diff_path", "changed_mechanisms",
        "dependency_runtime", "harness_relevance", "test_strength", "oracle_status",
        "proposed_candidates", "findings",
    ]
    import csv
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    queue = queue_from_rows(rows)
    (audit_dir / "screen_queue.txt").write_text("\n".join(queue) + ("\n" if queue else ""), encoding="utf-8")
    return {"rows": len(rows), "queue": queue, "csv": str(csv_path)}
