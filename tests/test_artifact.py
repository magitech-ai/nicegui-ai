"""Tests for artifact module."""

from nicegui_ai.artifact import ArtifactCard


def test_artifact_card_init():
    card = ArtifactCard(
        title="Test",
        artifact_type="file",
        content="content",
        language="python",
        size_bytes=100,
    )
    assert card.title == "Test"
    assert card.artifact_type == "file"
    assert not card.is_open


def test_artifact_card_toggle():
    card = ArtifactCard(title="Test", artifact_type="file", content="c")
    assert not card.is_open
    card.toggle()
    assert card.is_open
    card.toggle()
    assert not card.is_open
