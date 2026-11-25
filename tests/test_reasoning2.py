"""Tests for reasoning uncovered branches."""

from nicegui_ai.reasoning import ReasoningCard


def test_reasoning_card_defaults():
    card = ReasoningCard()
    assert card.thought_text == ""
    assert card.step_count == 1


def test_reasoning_card_append_empty():
    card = ReasoningCard(thought_text="Start", step_count=0)
    card.append_thought("", step_count=1)
    assert card.step_count == 1
