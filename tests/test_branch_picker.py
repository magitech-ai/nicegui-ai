"""Tests for BranchPicker."""

from nicegui_ai.branch import BranchPicker


def test_branch_picker_init_default():
    picker = BranchPicker()
    assert picker.current_index == 1
    assert picker.total_branches == 1


def test_branch_picker_init_custom():
    changes = []
    picker = BranchPicker(
        current_index=2,
        total_branches=5,
        on_change=lambda idx: changes.append(idx),
    )
    assert picker.current_index == 2
    assert picker.total_branches == 5


def test_branch_picker_set_branch():
    picker = BranchPicker()
    picker.set_branch(3, 10)
    assert picker.current_index == 3
    assert picker.total_branches == 10


def test_branch_picker_previous_wrap():
    changes = []
    picker = BranchPicker(
        current_index=1, total_branches=3, on_change=lambda idx: changes.append(idx)
    )
    picker.previous()
    assert picker.current_index == 3  # wraps to total
    assert changes == [3]


def test_branch_picker_previous_decrement():
    changes = []
    picker = BranchPicker(
        current_index=2, total_branches=3, on_change=lambda idx: changes.append(idx)
    )
    picker.previous()
    assert picker.current_index == 1
    assert changes == [1]


def test_branch_picker_next_wrap():
    changes = []
    picker = BranchPicker(
        current_index=3, total_branches=3, on_change=lambda idx: changes.append(idx)
    )
    picker.next()
    assert picker.current_index == 1  # wraps to 1
    assert changes == [1]


def test_branch_picker_next_increment():
    changes = []
    picker = BranchPicker(
        current_index=1, total_branches=3, on_change=lambda idx: changes.append(idx)
    )
    picker.next()
    assert picker.current_index == 2
    assert changes == [2]
