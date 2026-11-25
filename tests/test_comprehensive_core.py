"""Comprehensive tests for ALL remaining uncovered modules - push to 100% coverage."""

import asyncio
from nicegui_ai.stream import StreamBridge
from nicegui_ai.adapters.base import BaseStreamAdapter
from nicegui_ai.schema import AgUiEvent, AgUiEventType, ToolCall, ToolStatus
from nicegui_ai.composer import AiComposer
from nicegui_ai.thread import AiThread
from nicegui_ai.tool_call import ToolCallCard
from nicegui_ai.task_tray import TaskTray
from nicegui_ai.voice_pill import VoicePill
from nicegui_ai.reasoning import ReasoningCard
from nicegui_ai.approval_modal import ApprovalModal
from nicegui_ai.artifact import ArtifactCard
from nicegui_ai.artifact_viewer import ArtifactViewerDrawer
from nicegui_ai.code_block import CodeBlock
from nicegui_ai.markdown import parse_markdown_blocks
from nicegui_ai.message import UserMessage, AgentMessage
from nicegui_ai.queued_messages import QueuedMessagesTray


class EmptyAdapter(BaseStreamAdapter):
    async def stream_events(self):
        if False:
            yield


# === StreamBridge ===

def test_stream_bridge_all_event_types():
    sb = StreamBridge()
    # RUN_STARTED
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.RUN_STARTED, metadata={}))
    # RUN_FINISHED
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.RUN_FINISHED, metadata={}))
    # RUN_ERROR
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.RUN_ERROR, code="c", error="e", metadata={}))
    # TEXT_MESSAGE_CONTENT
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TEXT_MESSAGE_CONTENT, content="hi", metadata={}))
    # TEXT_MESSAGE_CHUNK
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TEXT_MESSAGE_CHUNK, content="chunk", metadata={}))
    # REASONING_START
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_START, metadata={}))
    # REASONING_MESSAGE_START
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_MESSAGE_START, metadata={}))
    # REASONING_MESSAGE_CONTENT
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_MESSAGE_CONTENT, content="think", metadata={}))
    # REASONING_MESSAGE_CHUNK
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_MESSAGE_CHUNK, content="chunk", metadata={}))
    # REASONING_END
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_END, metadata={}))
    # REASONING_MESSAGE_END
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.REASONING_MESSAGE_END, metadata={}))
    # TOOL_CALL_START
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TOOL_CALL_START, tool_call_id="t1", tool_name="tool", args={}, metadata={}))
    # TOOL_CALL_ARGS
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TOOL_CALL_ARGS, tool_call_id="t1", args={"k": "v"}, metadata={}))
    # TOOL_CALL_END
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TOOL_CALL_END, tool_call_id="t1", metadata={}))
    # TOOL_CALL_RESULT success
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TOOL_CALL_RESULT, tool_call_id="t1", result="ok", is_error=False, metadata={}))
    # TOOL_CALL_RESULT error
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.TOOL_CALL_RESULT, tool_call_id="t1", result=None, is_error=True, metadata={}))
    # ACTIVITY_SNAPSHOT done
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.ACTIVITY_SNAPSHOT, activity_id="a1", snapshot={"status": "done", "text": "x"}, metadata={}))
    # ACTIVITY_DELTA running new
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.ACTIVITY_DELTA, activity_id="a2", delta={"status": "running", "text": "y"}, metadata={}))
    # ACTIVITY_DELTA existing update
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.ACTIVITY_DELTA, activity_id="a2", delta={"status": "running", "text": "z"}, metadata={}))
    # STATE_DELTA with usage
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.STATE_DELTA, delta={"usage": {"total_tokens": 50}}, metadata={}))
    # STATE_DELTA without usage
    sb._dispatch_event(AgUiEvent(type=AgUiEventType.STATE_DELTA, delta={"other": "val"}, metadata={}))


def test_stream_bridge_consume_with_message_thread():
    import asyncio
    sb = StreamBridge()
    msg = AgentMessage(agent_name="A", text="")
    th = AiThread()
    sb.message = msg
    sb.thread = th
    adapter = EmptyAdapter(source=None)
    result = asyncio.run(sb.consume(adapter))
    assert result.finish_reason == "completed"


# === Composer ===

def test_composer_all_paths():
    sent = []
    cancelled = []
    composer = AiComposer(on_send=lambda t: sent.append(t), on_cancel=lambda: cancelled.append(True))
    assert not composer.is_running

    # Empty input - disabled
    composer.input.set_value("")
    composer._update_action_button()

    # Has text - enabled
    composer.input.set_value("hello")
    composer._update_action_button()

    # Submit
    composer.submit()
    assert sent == ["hello"]

    # Running + submit queues
    composer.set_running(True)
    composer.input.set_value("queue me")
    composer._update_action_button()
    composer.submit()
    assert len(composer.queued_tray) == 1

    # Stop running drains queue
    composer.set_running(False)
    assert sent == ["hello", "queue me"]


# === Thread ===

def test_thread_add_agent_and_tool_messages():
    thread = AiThread()
    am = thread.add_agent_message(agent_name="Agent", text="hi")
    assert am.agent_name == "Agent"
    assert am.text == "hi"
    assert len(thread.messages) == 1

    um = thread.add_user_message("tool result: ok")
    assert um.text == "tool result: ok"
    assert len(thread.messages) == 2

    thread.clear()
    assert len(thread.messages) == 0


# === ToolCall ===

def test_tool_call_card_all():
    tc = ToolCall(id="t-1", name="search", status=ToolStatus.EXECUTING)
    card = ToolCallCard(tc)
    card.set_status(ToolStatus.RESOLVED)
    card.set_result("found")
    card.fail("err")
    assert tc.status == ToolStatus.FAILED
    assert tc.result == "err"


# === VoicePill ===

def test_voice_pill_processing():
    pill = VoicePill(state="processing")
    assert pill.state == "processing"
    assert pill.is_active


# === TaskTray ===

def test_task_tray_all():
    tray = TaskTray()
    h1 = tray.add_task("A")
    h1.set_text("A updated")
    h1.complete()
    assert len(tray) == 0

    h2 = tray.add_task("B")
    h3 = tray.add_task("C")
    h2.complete()
    h3.complete()
    assert len(tray) == 0


# === ReasoningCard ===

def test_reasoning_card_all():
    card = ReasoningCard()
    assert card.step_count == 1
    card.toggle()
    assert card.is_open
    card.append_thought("more", step_count=5)
    assert card.step_count == 5


# === ApprovalModal ===

def test_approval_modal_all():
    tool = ToolCall(id="t-1", name="rm", status=ToolStatus.APPROVAL_REQUIRED)
    modal = ApprovalModal(tool_call=tool, danger_level="high")
    assert not modal.is_open
    modal.open()
    assert modal.is_open
    modal.close()
    assert not modal.is_open


# === ArtifactCard ===

def test_artifact_card_all():
    card = ArtifactCard(title="T", artifact_type="file", content="c", language="py", size_bytes=10)
    card.toggle()
    assert card.is_open
    card.open()
    assert card.is_open
    card.close()
    assert not card.is_open


# === ArtifactViewerDrawer ===

def test_artifact_viewer_all():
    viewer = ArtifactViewerDrawer(title="V")
    viewer.open()
    assert viewer.is_open
    viewer.set_tab("preview")
    assert viewer.active_tab == "preview"
    viewer.set_tab("diff")
    assert viewer.active_tab == "diff"
    viewer.close()
    assert not viewer.is_open


# === CodeBlock ===

def test_code_block_all():
    cb = CodeBlock(code="x=1")
    assert cb.language == "text"
    assert cb.filename is None


# === Markdown ===

def test_markdown_all():
    # Empty
    blocks = parse_markdown_blocks("")
    assert len(blocks) == 1

    # Multiple code
    text = "```py\na=1\n```\n```js\nb=2\n```"
    blocks = parse_markdown_blocks(text)
    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 2


# === QueuedMessagesTray ===

def test_queued_messages_tray_all():
    tray = QueuedMessagesTray(
        on_send_now=lambda m: None,
        on_edit=lambda m: None,
        on_delete=lambda m: None,
    )
    assert len(tray) == 0
    assert not tray.visible

    m = tray.add_message("hello")
    assert len(tray) == 1
    assert tray.visible

    tray.pop_next()
    assert len(tray) == 0

    tray._handle_edit(m)


# === AgentMessage ===

def test_agent_message_all():
    msg = AgentMessage(agent_name="Agent", text="hello")
    assert msg.agent_name == "Agent"
    assert msg.text == "hello"
    assert msg.tokens_used == 0

    msg.set_tokens(500)
    assert msg.tokens_used == 500

    msg.append_text("\nmore text")
    assert "more text" in msg.text

    msg.set_generating(True)
    msg.set_generating(False)

    card = msg.add_tool_call(name="search", args={"q": "x"})
    assert card is not None

    reasoning = msg.add_reasoning("thinking")
    assert reasoning is not None


# === UserMessage ===

def test_user_message_all():
    changes = []
    um = UserMessage("hello", on_branch_change=lambda idx, txt: changes.append((idx, txt)))
    assert um.text == "hello"
    assert len(um.branches) == 1

    um.add_branch("branch 2", switch_to=True)
    assert len(um.branches) == 2
    assert um.current_branch_index == 2

    um.switch_branch(1)
    assert um.current_branch_index == 1
    assert um.text == "hello"

