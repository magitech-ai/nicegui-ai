"""Reactive application state models for Magitech Harness (MTH)."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ToolExecutionStatus(StrEnum):
    """Lifecycle states of an agent tool call."""

    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MthSessionStats:
    """Session-level activity and token metrics matching the reference stats model."""

    turns: int = 0
    steps: int = 0
    llm_ms: float = 0.0
    tool_ms: float = 0.0
    ttft_ms: float = 0.0
    ttft_steps: int = 0
    decode_ms: float = 0.0
    decode_tokens: int = 0
    uncached_input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0

    def tokens_per_second(self) -> float:
        """Calculate token decoding speed in tokens/second."""
        if self.decode_ms <= 0:
            return 0.0
        return self.decode_tokens / (self.decode_ms / 1000.0)

    def billed_input_tokens(self) -> int:
        """Sum total billed input tokens across uncached and cached buckets."""
        return (
            self.uncached_input_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )

    def total_tokens(self) -> int:
        """Sum all input and output tokens across the session."""
        return self.billed_input_tokens() + self.output_tokens

    def cache_hit_percent(self) -> float | None:
        """Calculate cache-hit ratio percentage over billed input tokens."""
        denom = self.billed_input_tokens()
        if denom <= 0:
            return None
        return round((self.cache_read_tokens / denom) * 100.0, 1)


@dataclass
class MthDiffItem:
    """Document and unified diff inspection item."""

    file_path: str
    old_content: str | None = None
    new_content: str | None = None
    diff_text: str = ""
    added_lines: int = 0
    removed_lines: int = 0


@dataclass
class MthToolCallItem:
    """Structured representation of an invoked tool call."""

    call_id: str
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    status: ToolExecutionStatus = ToolExecutionStatus.PENDING
    result: str | None = None
    error: str | None = None
    approval_required: bool = False
    approved: bool | None = None


@dataclass
class MthTurnItem:
    """Discrete conversation turn consisting of user directive and agent execution."""

    turn_id: str
    user_text: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "idle"  # idle, executing, completed, aborted, failed
    reasoning: list[str] = field(default_factory=list)
    reasoning_duration_ms: float = 0.0
    is_deliberating: bool = False
    assistant_text: str = ""
    tool_calls: list[MthToolCallItem] = field(default_factory=list)
    tokens_used: int = 0
    uncached_input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    model_name: str = ""
    is_compacted: bool = False
    compaction_summary: str | None = None
    compaction_folded_count: int = 0


def format_clock_time(iso_str: str) -> str:
    """Format an ISO timestamp into a user-friendly clock time (e.g. '10:45 PM')."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone().strftime("%-I:%M %p")
    except Exception:
        return ""


def format_tokens(value: int) -> str:
    """Format token counts using compact notation (e.g. 500, 1.2K, 45K, 1.5M)."""
    if value < 1000:
        return str(value)
    if value < 1_000_000:
        k = value / 1000.0
        return f"{k:.0f}K" if k >= 100 else f"{k:.1f}K"
    m = value / 1_000_000.0
    return f"{m:.0f}M" if m >= 100 else f"{m:.1f}M"


@dataclass
class MthAttachment:
    """Attachment file or image item for the prompt composer."""

    id: str
    name: str
    size_bytes: int = 0
    media_type: str = "text/plain"
    is_image: bool = False
    data_url: str | None = None
    upload_status: str = "ready"  # ready, uploading, error


@dataclass
class MthCommandItem:
    """Command specification for the composer fastpicker and slash command registry."""

    token: str
    name: str
    description: str
    category: str = "General"
    badge: str | None = None


@dataclass
class MthContextOccupancy:
    """Token pressure and breakdown of the current model context window."""

    used_tokens: int = 0
    context_window: int = 128000
    system_tokens: int = 0
    tools_tokens: int = 0
    message_tokens: int = 0

    def percent(self) -> float:
        """Calculate occupancy percentage bounded between 0 and 100."""
        if self.context_window <= 0:
            return 0.0
        return min(100.0, round((self.used_tokens / self.context_window) * 100.0, 1))


def format_relative_time(iso_str: str) -> str:
    """Format an ISO timestamp into compact relative time ('just now', '5m', '2h', '1d', etc.)."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        diff = (datetime.now(UTC) - dt).total_seconds()
        if diff < 60:
            return "just now"
        if diff < 3600:
            return f"{int(diff // 60)}m"
        if diff < 86400:
            return f"{int(diff // 3600)}h"
        if diff < 604800:
            return f"{int(diff // 86400)}d"
        return dt.strftime("%b %d")
    except Exception:
        return "recently"


@dataclass
class MthSession:
    """Append-only persistent record of interaction events."""

    id: str
    title: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    tokens_used: int = 0
    workspace: str = "default"
    pinned: bool = False
    archived: bool = False
    status: str = "idle"  # idle, running
    turns: list[MthTurnItem] = field(default_factory=list)


class MthAppState:
    """Centralized reactive state manager for the MTH application shell."""

    def __init__(
        self,
        active_profile: str = "default",
        profiles: list[str] | None = None,
        sessions: list[MthSession] | None = None,
        workspace_root: str = ".",
        current_model: str = "default-chat",
        available_models: list[str] | None = None,
        permission_preset: str = "auto",
    ) -> None:
        self.active_profile = active_profile
        self.profiles = profiles or ["default", "code", "research"]
        self.sessions: list[MthSession] = sessions or []
        self.active_session_id: str | None = (
            self.sessions[0].id if self.sessions else None
        )
        self.is_running: bool = False
        self.metrics = MthSessionStats()
        self.sidebar_collapsed: bool = False
        self.inspector_open: bool = False
        self.inspector_active_tab: str = "diff"
        self.active_diff: MthDiffItem | None = None
        self.workspace_root = workspace_root

        # Composer & execution mode states
        self.current_model = current_model
        self.available_models = available_models or [
            "default-chat",
            "reasoner-pro",
            "gpt-4o",
            "claude-3-5-sonnet",
        ]
        self.reasoning_effort: str = "medium"
        self.permission_preset: str = permission_preset
        self.plan_mode: bool = False
        self.attachments: list[MthAttachment] = []
        self.context_occupancy = MthContextOccupancy()

    def set_model(self, model: str) -> None:
        """Set the active model."""
        self.current_model = model

    def set_reasoning_effort(self, effort: str) -> None:
        """Set reasoning deliberation effort level."""
        self.reasoning_effort = effort

    def set_permission_preset(self, preset: str) -> None:
        """Set execution authorization preset."""
        self.permission_preset = preset

    def toggle_plan_mode(self) -> bool:
        """Toggle planning mode active status."""
        self.plan_mode = not self.plan_mode
        return self.plan_mode

    def add_attachment(self, attachment: MthAttachment) -> None:
        """Add an attachment item."""
        self.attachments.append(attachment)

    def remove_attachment(self, attachment_id: str) -> bool:
        """Remove an attachment item by id."""
        for att in self.attachments:
            if att.id == attachment_id:
                self.attachments.remove(att)
                return True
        return False

    def clear_attachments(self) -> None:
        """Clear all active composer attachments."""
        self.attachments.clear()

    def toggle_sidebar(self) -> bool:
        """Toggle left sidebar between collapsed rail and expanded drawer."""
        self.sidebar_collapsed = not self.sidebar_collapsed
        return self.sidebar_collapsed

    def toggle_inspector(self) -> bool:
        """Toggle right inspector panel open/close."""
        self.inspector_open = not self.inspector_open
        return self.inspector_open

    def set_active_diff(self, diff: MthDiffItem) -> None:
        """Set the active diff item and open inspector on the diff tab."""
        self.active_diff = diff
        self.inspector_active_tab = "diff"
        self.inspector_open = True

    def create_session(
        self, title: str = "New Session", workspace: str = "default"
    ) -> MthSession:
        """Create and activate a new session."""
        session = MthSession(
            id=str(uuid.uuid4())[:8],
            title=title,
            workspace=workspace,
        )
        self.sessions.insert(0, session)
        self.active_session_id = session.id
        return session

    def get_session(self, session_id: str) -> MthSession | None:
        """Retrieve a session by its id."""
        for s in self.sessions:
            if s.id == session_id:
                return s
        return None

    def pin_session(self, session_id: str) -> bool:
        """Toggle the pinned state of a session."""
        sess = self.get_session(session_id)
        if sess:
            sess.pinned = not sess.pinned
            sess.updated_at = datetime.now(UTC).isoformat()
            return sess.pinned
        return False

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a session."""
        sess = self.get_session(session_id)
        if sess and new_title.strip():
            sess.title = new_title.strip()
            sess.updated_at = datetime.now(UTC).isoformat()

    def fork_session(self, session_id: str) -> MthSession | None:
        """Fork a session by duplicating its historical turns into a new active branch."""
        parent = self.get_session(session_id)
        if not parent:
            return None
        forked = MthSession(
            id=str(uuid.uuid4())[:8],
            title=f"Fork of {parent.title}",
            workspace=parent.workspace,
            tokens_used=parent.tokens_used,
            turns=list(parent.turns),
        )
        self.sessions.insert(0, forked)
        self.active_session_id = forked.id
        return forked

    def archive_session(self, session_id: str) -> bool:
        """Toggle the archived status of a session."""
        sess = self.get_session(session_id)
        if sess:
            sess.archived = not sess.archived
            sess.updated_at = datetime.now(UTC).isoformat()
            return sess.archived
        return False

    def delete_session(self, session_id: str) -> bool:
        """Remove a session from history and select an adjacent active session."""
        target = self.get_session(session_id)
        if not target:
            return False
        self.sessions.remove(target)
        if self.active_session_id == session_id:
            self.active_session_id = self.sessions[0].id if self.sessions else None
        return True

    def get_workspaces(self) -> list[str]:
        """Return list of distinct workspace names."""
        seen: set[str] = set()
        workspaces: list[str] = []
        for s in self.sessions:
            if s.workspace not in seen:
                seen.add(s.workspace)
                workspaces.append(s.workspace)
        return workspaces or ["default"]

    def get_active_session(self) -> MthSession | None:
        """Retrieve the currently active session object."""
        if not self.active_session_id:
            return None
        for s in self.sessions:
            if s.id == self.active_session_id:
                return s
        return None

    def add_turn(self, user_text: str) -> MthTurnItem:
        """Add a new turn to the active session."""
        session = self.get_active_session()
        if not session:
            session = self.create_session()

        turn = MthTurnItem(
            turn_id=str(uuid.uuid4())[:8],
            user_text=user_text,
        )
        session.turns.append(turn)
        session.updated_at = datetime.now(UTC).isoformat()
        return turn

    def get_active_turn(self) -> MthTurnItem | None:
        """Retrieve the latest turn in the active session."""
        session = self.get_active_session()
        if not session or not session.turns:
            return None
        return session.turns[-1]

    def add_tool_call(
        self,
        turn_id: str,
        call_id: str,
        name: str,
        args: dict[str, Any],
        approval_required: bool = False,
    ) -> MthToolCallItem:
        """Attach a tool call to a specific turn."""
        tool = MthToolCallItem(
            call_id=call_id,
            name=name,
            args=args,
            status=(
                ToolExecutionStatus.AWAITING_APPROVAL
                if approval_required
                else ToolExecutionStatus.PENDING
            ),
            approval_required=approval_required,
        )
        session = self.get_active_session()
        if session:
            for turn in session.turns:
                if turn.turn_id == turn_id:
                    turn.tool_calls.append(tool)
                    break
        return tool

    def resolve_tool_call(
        self,
        call_id: str,
        result: str,
        status: ToolExecutionStatus = ToolExecutionStatus.COMPLETED,
    ) -> None:
        """Resolve a tool call with its execution output."""
        session = self.get_active_session()
        if not session:
            return
        for turn in session.turns:
            for tool in turn.tool_calls:
                if tool.call_id == call_id:
                    tool.status = status
                    if status == ToolExecutionStatus.COMPLETED:
                        tool.result = result
                    else:
                        tool.error = result
                    return
