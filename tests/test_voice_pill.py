"""Tests for voice_pill module."""

from nicegui_ai.voice_pill import VoicePill


def test_voice_pill_init():
    pill = VoicePill(state="idle")
    assert pill.state == "idle"
    assert not pill.is_active


def test_voice_pill_listening():
    pill = VoicePill(state="listening")
    assert pill.state == "listening"
    assert pill.is_active


def test_voice_pill_speaking():
    pill = VoicePill(state="speaking")
    assert pill.state == "speaking"
    assert pill.is_active


def test_voice_pill_set_state():
    pill = VoicePill()
    pill.set_state("listening")
    assert pill.state == "listening"
    assert pill.is_active
    pill.set_state("idle")
    assert pill.state == "idle"
    assert not pill.is_active
