"""Tests for approval_modal module."""

from nicegui_ai.approval_modal import ApprovalModal
from nicegui_ai.schema import ToolCall, ToolStatus


def test_approval_modal_init():
    tool = ToolCall(id="t-1", name="delete", status=ToolStatus.APPROVAL_REQUIRED)
    modal = ApprovalModal(tool_call=tool, danger_level="critical")
    assert modal.tool_call == tool
    assert modal.danger_level == "critical"
    assert not modal.is_open


def test_approval_modal_open_close():
    tool = ToolCall(id="t-1", name="delete", status=ToolStatus.APPROVAL_REQUIRED)
    modal = ApprovalModal(tool_call=tool)
    assert not modal.is_open
    modal.open()
    assert modal.is_open
    modal.close()
    assert not modal.is_open
