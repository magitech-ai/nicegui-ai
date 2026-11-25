"""Tests for stream adapters with full state accumulation coverage."""

import pytest
from nicegui_ai.adapters.agui import AgUiStreamAdapter
from nicegui_ai.adapters.base import BaseStreamAdapter
from nicegui_ai.adapters.gemini import GeminiStreamAdapter
from nicegui_ai.adapters.opencode import OpenCodeStreamAdapter
from nicegui_ai.adapters.openrouter import OpenRouterStreamAdapter
from nicegui_ai.schema import (
    AgUiEvent,
    AgUiEventType,
    ToolCall,
    ToolStatus,
)


def _make_text_event(content="hello", metadata=None):
    return AgUiEvent(
        type=AgUiEventType.TEXT_MESSAGE_CONTENT,
        content=content,
        metadata=metadata or {},
    )


def _make_reasoning_event(content="thinking", metadata=None):
    return AgUiEvent(
        type=AgUiEventType.REASONING_MESSAGE_CONTENT,
        content=content,
        metadata=metadata or {},
    )


def _make_tool_start(tid="t1", name="tool", args=None, metadata=None):
    return AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        tool_call_id=tid,
        tool_name=name,
        args=args or {},
        metadata=metadata or {},
    )


def _make_tool_args(tid="t1", args=None, metadata=None):
    return AgUiEvent(
        type=AgUiEventType.TOOL_CALL_ARGS,
        tool_call_id=tid,
        args=args or {},
        metadata=metadata or {},
    )


def _make_tool_end(tid="t1", metadata=None):
    return AgUiEvent(type=AgUiEventType.TOOL_CALL_END, tool_call_id=tid, metadata=metadata or {})


def _make_tool_result(tid="t1", result="ok", is_error=False, metadata=None):
    return AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        tool_call_id=tid,
        result=result,
        is_error=is_error,
        metadata=metadata or {},
    )


def _make_run_finished(reason="stop", metadata=None):
    return AgUiEvent(
        type=AgUiEventType.RUN_FINISHED,
        metadata={"finish_reason": reason, **(metadata or {})},
    )


def _make_run_error(code="err", message="failed", metadata=None):
    return AgUiEvent(
        type=AgUiEventType.RUN_ERROR,
        code=code,
        error=message,
        metadata=metadata or {},
    )


class ConcreteAdapter(BaseStreamAdapter):
    """Concrete adapter for testing base class state accumulation."""

    async def stream_events(self):
        if False:
            yield  # pragma: no cover


def test_base_adapter_text_chunk():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_text_event("hello"))
    assert adapter.text == "hello"


def test_base_adapter_reasoning_chunk():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_reasoning_event("thinking"))
    assert adapter.thought == "thinking"


def test_base_adapter_tool_start():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_tool_start("t1", "search", {"q": "x"}))
    assert len(adapter.tool_calls) == 1
    assert adapter.tool_calls[0].name == "search"
    assert adapter.tool_calls[0].args == {"q": "x"}


def test_base_adapter_tool_args_update():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_tool_start("t1", "search", {"q": "x"}))
    adapter._accumulate_state(_make_tool_args("t1", {"extra": "y"}))
    assert adapter.tool_calls[0].args == {"q": "x", "extra": "y"}


def test_base_adapter_tool_end():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_tool_start("t1", "search"))
    adapter._accumulate_state(_make_tool_end("t1"))


def test_base_adapter_tool_result_resolved():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_tool_start("t1", "search"))
    adapter._accumulate_state(_make_tool_result("t1", "found", is_error=False))
    assert adapter.tool_calls[0].status == ToolStatus.RESOLVED
    assert adapter.tool_calls[0].result == "found"


def test_base_adapter_tool_result_failed():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_tool_start("t1", "search"))
    adapter._accumulate_state(_make_tool_result("t1", None, is_error=True))
    assert adapter.tool_calls[0].status == ToolStatus.FAILED


def test_base_adapter_run_finished():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_run_finished("stop"))
    assert adapter.finish_reason == "stop"


def test_base_adapter_run_error():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(_make_run_error("code", "failed"))
    assert adapter.error == "failed"


def test_base_adapter_metadata_usage():
    adapter = ConcreteAdapter(source=None)
    adapter._accumulate_state(
        _make_text_event("x", metadata={"usage": {"tokens": 100}})
    )
    assert adapter.usage == {"tokens": 100}


def test_adapter_init_all():
    for cls in (
        AgUiStreamAdapter,
        GeminiStreamAdapter,
        OpenCodeStreamAdapter,
        OpenRouterStreamAdapter,
    ):
        adapter = cls(source=None)
        assert adapter.source is None
        assert adapter.text == ""
        assert adapter.thought == ""
        assert adapter.tool_calls == []
        assert adapter.events == []
