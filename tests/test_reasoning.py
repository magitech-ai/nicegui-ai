"""Tests for reasoning module."""

from nicegui_ai.reasoning import ReasoningCard


def test_reasoning_card_init():
    card = ReasoningCard(thought_text="Initial", step_count=1)
    assert card.thought_text == "Initial"
    assert card.step_count == 1
    assert not card.is_open


def test_reasoning_card_toggle():
    card = ReasoningCard(thought_text="Initial")
    assert not card.is_open
    card.toggle()
    assert card.is_open
    card.toggle()
    assert not card.is_open


def test_reasoning_card_append_thought():
    card = ReasoningCard(thought_text="First", step_count=1)
    card.append_thought("\nSecond", step_count=2)
    assert card.step_count == 2
    assert "First" in card.thought_text
    assert "Second" in card.thought_text
