"""Tests for approval_modal, artifact, code_block, markdown, reasoning, tool_call, voice_pill."""

from nicegui_ai.approval_modal import ApprovalModal
from nicegui_ai.artifact import ArtifactCard
from nicegui_ai.code_block import CodeBlock
from nicegui_ai.markdown import parse_markdown_blocks
from nicegui_ai.reasoning import ReasoningCard
from nicegui_ai.schema import ToolCall, ToolStatus
from nicegui_ai.tool_call import ToolCallCard
from nicegui_ai.voice_pill import VoicePill


def test_approval_modal_all_states():
    tool = ToolCall(id="t-1", name="delete", status=ToolStatus.APPROVAL_REQUIRED)
    modal = ApprovalModal(tool_call=tool, danger_level="critical")
    assert not modal.is_open
    modal.open()
    assert modal.is_open
    modal.close()
    assert not modal.is_open
    modal.open()
    modal.close()


def test_artifact_card_states():
    card = ArtifactCard(title="T", artifact_type="file", content="c")
    assert not card.is_open
    card.toggle()
    assert card.is_open
    card.close()
    assert not card.is_open
    card.open()
    assert card.is_open


def test_code_block_all():
    b = CodeBlock(code="x=1")
    assert b.language == "text"
    assert b.filename is None
    b = CodeBlock(code="x=1", language="py", filename="f.py")
    assert b.language == "py"
    assert b.filename == "f.py"


def test_markdown_all():
    # Empty
    blocks = parse_markdown_blocks("")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "text"

    # Multiple code blocks
    text = "```py\nprint(1)\n```\n```js\nconsole.log(1)\n```"
    blocks = parse_markdown_blocks(text)
    code = [b for b in blocks if b["type"] == "code"]
    assert len(code) == 2


def test_reasoning_card_states():
    card = ReasoningCard()
    assert card.step_count == 1
    card.toggle()
    assert card.is_open
    card.append_thought("more", step_count=2)
    assert card.step_count == 2


def test_tool_call_full():
    tc = ToolCall(id="t-1", name="search", status=ToolStatus.EXECUTING)
    card = ToolCallCard(tc)
    card.set_status(ToolStatus.RESOLVED)
    card.set_result("found")
    card.fail("timeout")
    assert tc.status == ToolStatus.FAILED
    assert tc.result == "timeout"


def test_voice_pill_all():
    pill = VoicePill()
    assert pill.state == "idle"
    assert not pill.is_active
    pill.set_state("listening")
    assert pill.is_active
    pill.set_state("speaking")
    assert pill.is_active
    pill.set_state("idle")
    assert not pill.is_active
