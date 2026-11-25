"""Magitech Harness (MTH) Desktop & Web UI components for NiceGUI."""

from .adapter import MthStreamAdapter
from .app import MthApp
from .command_picker import DEFAULT_COMMANDS, MthCommandFastpicker
from .composer import MthComposer, MthModelSelectDialog
from .context_meter import MthContextBreakdownDialog, MthContextMeter
from .inspector_drawer import (
    MthDiffPreview,
    MthFileTree,
    MthInspectorDrawer,
    MthTerminalDock,
    generate_unified_diff,
)
from .session_drawer import MthSessionDrawer, MthSessionRow
from .state import (
    MthAppState,
    MthAttachment,
    MthCommandItem,
    MthContextOccupancy,
    MthDiffItem,
    MthSession,
    MthSessionStats,
    MthToolCallItem,
    MthTurnItem,
    ToolExecutionStatus,
    format_clock_time,
    format_relative_time,
    format_tokens,
)
from .stats_pills import MthStatsPills, format_duration
from .theme import MTH_THEME_CSS, setup_mth_theme
from .timeline import (
    MthAssistantBubble,
    MthCompactionItem,
    MthReasoningRow,
    MthRunningTail,
    MthTimeline,
    MthTurnNavigator,
    MthTurnUsageDialog,
    MthUserBubble,
    clean_first_line,
)
from .tool_card import (
    AskQuestionToolCard,
    BashToolCard,
    FileMutationToolCard,
    MthApprovalPanel,
    MthToolCard,
    ReadToolCard,
    create_tool_card,
)

__all__ = [
    "AskQuestionToolCard",
    "BashToolCard",
    "DEFAULT_COMMANDS",
    "FileMutationToolCard",
    "MTH_THEME_CSS",
    "MthApp",
    "MthAppState",
    "MthApprovalPanel",
    "MthAssistantBubble",
    "MthAttachment",
    "MthCommandFastpicker",
    "MthCommandItem",
    "MthCompactionItem",
    "MthComposer",
    "MthContextBreakdownDialog",
    "MthContextMeter",
    "MthContextOccupancy",
    "MthDiffItem",
    "MthDiffPreview",
    "MthFileTree",
    "MthInspectorDrawer",
    "MthModelSelectDialog",
    "MthReasoningRow",
    "MthRunningTail",
    "MthSession",
    "MthSessionDrawer",
    "MthSessionRow",
    "MthSessionStats",
    "MthStatsPills",
    "MthStreamAdapter",
    "MthTerminalDock",
    "MthTimeline",
    "MthToolCard",
    "MthToolCallItem",
    "MthTurnItem",
    "MthTurnNavigator",
    "MthTurnUsageDialog",
    "MthUserBubble",
    "ReadToolCard",
    "ToolExecutionStatus",
    "clean_first_line",
    "create_tool_card",
    "format_clock_time",
    "format_duration",
    "format_relative_time",
    "format_tokens",
    "generate_unified_diff",
    "setup_mth_theme",
]
