"""Tests for StreamBridge."""

import asyncio
from nicegui_ai.stream import StreamBridge
from nicegui_ai.adapters.base import BaseStreamAdapter
from nicegui_ai.schema import AgUiEvent, AgUiEventType


class EmptyAdapter(BaseStreamAdapter):
    async def stream_events(self):
        if False:
            yield


def test_stream_bridge_init():
    sb = StreamBridge()
    assert sb.message is None
    assert sb.thread is None
    assert sb.header is None
    assert sb.composer is None
    assert sb.task_tray is None


def test_stream_bridge_from_adapters():
    assert StreamBridge.from_openrouter(None) is not None
    assert StreamBridge.from_gemini(None) is not None
    assert StreamBridge.from_agui(None) is not None
    assert StreamBridge.from_opencode(None) is not None


def test_stream_bridge_consume_empty():
    import asyncio

    sb = StreamBridge()
    adapter = EmptyAdapter(source=None)
    result = asyncio.run(sb.consume(adapter))
    assert result.text == ""
    assert result.finish_reason == "completed"
    assert result.error is None


def test_stream_bridge_dispatch_run_started():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.RUN_STARTED, metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_run_finished():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.RUN_FINISHED, metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_run_error():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.RUN_ERROR, code="err", error="failed", metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_text():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.TEXT_MESSAGE_CONTENT, content="hello", metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_reasoning_start():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.REASONING_START, metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_reasoning_content():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.REASONING_MESSAGE_CONTENT, content="thinking", metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_reasoning_end():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.REASONING_END, metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_tool_start():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        tool_call_id="t1",
        tool_name="search",
        args={"q": "x"},
        metadata={},
    )
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_tool_args():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.TOOL_CALL_ARGS,
        tool_call_id="t1",
        args={"q": "y"},
        metadata={},
    )
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_tool_end():
    sb = StreamBridge()
    event = AgUiEvent(type=AgUiEventType.TOOL_CALL_END, tool_call_id="t1", metadata={})
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_tool_result():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        tool_call_id="t1",
        result="ok",
        is_error=False,
        metadata={},
    )
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_activity_snapshot():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.ACTIVITY_SNAPSHOT,
        activity_id="a1",
        snapshot={"status": "done", "text": "done"},
        metadata={},
    )
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_activity_delta():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.ACTIVITY_DELTA,
        activity_id="a1",
        delta={"status": "running", "text": "running"},
        metadata={},
    )
    sb._dispatch_event(event)


def test_stream_bridge_dispatch_state_delta():
    sb = StreamBridge()
    event = AgUiEvent(
        type=AgUiEventType.STATE_DELTA,
        delta={"usage": {"total_tokens": 100}},
        metadata={},
    )
    sb._dispatch_event(event)
