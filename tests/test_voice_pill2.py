"""Tests for voice_pill uncovered branches."""

from nicegui_ai.voice_pill import VoicePill


def test_voice_pill_all_states():
    pill = VoicePill()
    for state in ["idle", "listening", "speaking", "processing"]:
        pill.set_state(state)
        assert pill.state == state
