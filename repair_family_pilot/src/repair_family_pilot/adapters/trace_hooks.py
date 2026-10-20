"""Structured event log injected into a case subprocess."""

from __future__ import annotations

import json
from pathlib import Path


_PATH: Path | None = None


def install(event_path: str) -> None:
    global _PATH
    _PATH = Path(event_path)
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text("", encoding="utf-8")
    _wrap_optional_clients()


def _request_view(kwargs: dict) -> dict:
    reasoning = kwargs.get("reasoning_effort")
    if reasoning is None and isinstance(kwargs.get("reasoning"), dict):
        reasoning = kwargs["reasoning"].get("effort")
    return {"model": kwargs.get("model"), "reasoning_effort": reasoning}


def _call_without_stop(create, args, kwargs):
    """gpt-6-luna rejects the stop sequences LangChain agents attach to a call."""
    forwarded = dict(kwargs)
    forwarded.pop("stop", None)
    return create(*args, **forwarded)


def _usage_from_mapping(usage: dict) -> dict:
    return {
        "input_tokens": int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or usage.get("completion_tokens") or 0),
    }


def _usage_view(result) -> dict | None:
    usage = getattr(result, "usage", None)
    if isinstance(usage, dict):
        return _usage_from_mapping(usage)
    if usage is not None:
        mapped = _usage_from_mapping(
            {
                "input_tokens": getattr(usage, "input_tokens", None),
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
            }
        )
        if mapped["input_tokens"] or mapped["output_tokens"]:
            return mapped
    http = getattr(result, "http_response", None)
    if http is not None:
        try:
            body = http.json()
        except Exception:
            body = None
        if isinstance(body, dict) and isinstance(body.get("usage"), dict):
            return _usage_from_mapping(body["usage"])
    return None


def _response_view(result) -> dict:
    text = getattr(result, "output_text", None)
    choices = getattr(result, "choices", None)
    if text is None and choices:
        message = getattr(choices[0], "message", None)
        text = getattr(message, "content", None) if message is not None else None
    return {"usage": _usage_view(result), "text": text}


def _emit(kind: str, payload) -> None:
    if _PATH is None:
        return
    with _PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": kind, "payload": payload}, default=str) + "\n")


def _message_view(messages: list) -> dict:
    contents = []
    roles = []
    for message in messages:
        if isinstance(message, str):
            contents.append(message)
            roles.append("str")
        else:
            contents.append(getattr(message, "content", str(message)))
            roles.append(getattr(message, "type", type(message).__name__))
    return {"contents": contents, "roles": roles}


def snapshot(module) -> None:
    payload = {}
    messages = getattr(module, "messages", None)
    if isinstance(messages, list):
        payload["messages"] = _message_view(messages)
    memory = getattr(module, "memory", None)
    stored = None
    if memory is not None:
        chat = getattr(memory, "chat_memory", None)
        stored = getattr(chat, "messages", None) if chat is not None else None
        if stored is None:
            stored = getattr(memory, "messages", None)
    if isinstance(stored, list):
        payload["memory"] = _message_view(stored)
    if payload:
        _emit("memory_snapshot", payload)


def termination(status: str, detail: str) -> None:
    _emit("termination", {"status": status, "detail": detail})


def _wrap_optional_clients() -> None:
    try:
        import openai
    except ImportError:
        openai = None
    if openai is not None and hasattr(openai, "OpenAI"):
        original = openai.OpenAI

        class RecordingOpenAI(original):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                create = self.chat.completions.create

                def wrapped(*cargs, **ckwargs):
                    _emit("model_request", _request_view(ckwargs))
                    result = _call_without_stop(create, cargs, ckwargs)
                    _emit("model_response", _response_view(result))
                    return result

                self.chat.completions.create = wrapped
                if hasattr(self, "responses"):
                    responses_create = self.responses.create

                    def wrapped_responses(*rcargs, **rckwargs):
                        _emit("model_request", _request_view(rckwargs))
                        result = _call_without_stop(responses_create, rcargs, rckwargs)
                        _emit("model_response", _response_view(result))
                        return result

                    self.responses.create = wrapped_responses

        openai.OpenAI = RecordingOpenAI
    try:
        import ollama
    except ImportError:
        ollama = None
    if ollama is not None and hasattr(ollama, "chat"):
        original_chat = ollama.chat

        def wrapped_chat(*args, **kwargs):
            _emit("model_request", {"args": args, "kwargs": kwargs})
            result = original_chat(*args, **kwargs)
            _emit("model_response", {"result": result})
            return result

        ollama.chat = wrapped_chat
