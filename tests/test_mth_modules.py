"""Tests for mth composer, timeline, stats_pills, context_meter, command_picker modules."""

from nicegui_ai.mth.command_picker import MthCommandFastpicker
from nicegui_ai.mth.composer import MthComposer
from nicegui_ai.mth.context_meter import MthContextMeter
from nicegui_ai.mth.stats_pills import MthStatsPills
from nicegui_ai.mth.timeline import MthTimeline


def test_mth_composer_init():
    composer = MthComposer()
    assert composer is not None


def test_mth_timeline_init():
    timeline = MthTimeline()
    assert timeline is not None


def test_mth_timeline_start_stop_running():
    timeline = MthTimeline()
    timeline.start_running_tail("Thinking...")
    timeline.stop_running_tail()


def test_mth_stats_pills_init():
    pills = MthStatsPills()
    assert pills is not None


def test_mth_context_meter_init():
    meter = MthContextMeter()
    assert meter is not None


def test_mth_command_picker_init():
    picker = MthCommandFastpicker()
    assert picker is not None
