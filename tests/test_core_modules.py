"""Tests for core modules."""

from nicegui_ai.approval_modal import ApprovalModal
from nicegui_ai.artifact import ArtifactCard
from nicegui_ai.artifact_viewer import ArtifactViewerDrawer
from nicegui_ai.code_block import CodeBlock
from nicegui_ai.composer import AiComposer
from nicegui_ai.markdown import parse_markdown_blocks
from nicegui_ai.message import UserMessage, AgentMessage
from nicegui_ai.stream import StreamBridge
from nicegui_ai.tool_call import ToolCall, ToolCallCard, ToolStatus


def test_approval_modal_full():
    tool = ToolCall(id="t-1", name="delete", status=ToolStatus.APPROVAL_REQUIRED)
    modal = ApprovalModal(tool_call=tool, danger_level="critical")
    assert modal.danger_level == "critical"
    modal.open()
    assert modal.is_open
    modal.close()
    assert not modal.is_open


def test_artifact_card_full():
    card = ArtifactCard(
        title="Test", artifact_type="file", content="c",
        language="python", size_bytes=100,
    )
    card.toggle()
    assert card.is_open
    card.close()
    assert not card.is_open


def test_artifact_viewer_full():
    viewer = ArtifactViewerDrawer(title="Test")
    viewer.open()
    assert viewer.is_open
    viewer.close()
    assert not viewer.is_open


def test_code_block_full():
    block = CodeBlock(code="x=1", language="python", filename="t.py")
    assert block.code == "x=1"


def test_composer_full():
    sent = []
    composer = AiComposer(on_send=lambda t: sent.append(t))
    composer.input.set_value("hi")
    composer.submit()
    assert sent == ["hi"]


def test_markdown_full():
    blocks = parse_markdown_blocks("text\n```py\nprint(1)\n```\nmore")
    assert len(blocks) == 3


def test_message_full():
    um = UserMessage("hello")
    assert um.text == "hello"
    am = AgentMessage(agent_name="A", text="hi")
    assert am.agent_name == "A"


def test_stream_bridge_init():
    sb = StreamBridge()
    assert sb is not None


def test_tool_call_full():
    tc = ToolCall(id="t-1", name="search", status=ToolStatus.EXECUTING)
    assert tc.name == "search"
    card = ToolCallCard(tc)
    card.set_status(ToolStatus.RESOLVED)
    card.set_result("ok")
    assert card.tool_call.status == ToolStatus.RESOLVED
    card.fail("err")
    assert card.tool_call.status == ToolStatus.FAILED
