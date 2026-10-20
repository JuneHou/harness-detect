"""Twelve task groups for case 76906469.

Each group is one cell of three dimensions: what must be remembered, how many
unrelated turns sit in between, and whether that information started in a user
turn or an assistant turn. A different country name alone is not a new group.
"""

from __future__ import annotations

FILLER = "Note {index}: the sky is blue."


def _fillers(count: int) -> list:
    return [FILLER.format(index=index + 1) for index in range(count)]


def build_suite() -> list:
    groups = []
    for needed in ("prior_question", "stated_capital"):
        for origin in ("user", "assistant"):
            for gap in (0, 2, 5):
                groups.append(_group(needed, origin, gap))
    return groups


def _group(needed: str, origin: str, gap: int) -> dict:
    group_id = f"{needed}-{origin}-gap{gap}"
    fillers = _fillers(gap)
    if needed == "prior_question" and origin == "user":
        turns = ["what is the capital of France?", *fillers, "Which country did my first question name?"]
        initial = []
        expected = "france"
    elif needed == "prior_question" and origin == "assistant":
        turns = [*fillers, "Which country did the earlier reply name?"]
        initial = [{"role": "ai", "content": "The earlier question named France."}]
        expected = "france"
    elif needed == "stated_capital" and origin == "user":
        turns = ["Please remember: the capital of Peru is Lima.", *fillers, "What capital did I tell you to remember?"]
        initial = []
        expected = "lima"
    else:
        turns = [*fillers, "What capital did the earlier reply give?"]
        initial = [{"role": "ai", "content": "The capital of Peru is Lima."}]
        expected = "lima"
    return {
        "group_id": group_id,
        "needed": needed,
        "origin": origin,
        "gap": gap,
        "turns": turns,
        "initial_memory": initial,
        "expected": expected,
    }
