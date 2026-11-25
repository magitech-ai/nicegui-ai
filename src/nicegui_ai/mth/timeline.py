"""Central conversation timeline, deliberation disclosure, turn navigation, and message chrome for Magitech Harness."""

import time
from collections.abc import Callable
from typing import Any

from nicegui import core, ui

from .state import MthTurnItem, format_clock_time
from .tool_card import create_tool_card


def clean_first_line(text: str) -> str:
    """Extract and sanitize first line of reasoning for collapsed summary preview."""
    if not text:
        return ""
    line = text.splitlines()[0] if text.splitlines() else ""
    return line.replace("**", "").strip()


class MthTurnUsageDialog:
    """Dialog displaying granular per-turn token accounting."""

    @staticmethod
    def show(turn: MthTurnItem) -> None:
        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "bg-[#11131a] border border-[#232736] text-slate-200 p-4 min-w-[320px] rounded-xl"
            ),
        ):
            with ui.row().classes(
                "w-full items-center justify-between border-b border-[#232736] pb-2 mb-3"
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("storage", size="16px").classes("text-emerald-400")
                    ui.label("Turn Token Accounting").classes(
                        "font-semibold text-sm text-white"
                    )
                ui.button(icon="close", on_click=dialog.close).props(
                    "dense flat round size=sm"
                )

            total_prompt = (
                turn.uncached_input_tokens
                + turn.cache_read_tokens
                + turn.cache_write_tokens
            )
            cache_hit = (
                round((turn.cache_read_tokens / total_prompt) * 100.0, 1)
                if total_prompt > 0
                else None
            )
            cache_hit_str = f"{cache_hit}%" if cache_hit is not None else "N/A"

            with ui.column().classes("w-full gap-2 text-xs font-mono"):
                if turn.model_name:
                    MthTurnUsageDialog._render_row(
                        "Model", turn.model_name, "text-blue-400"
                    )
                MthTurnUsageDialog._render_row(
                    "Total Tokens", f"{turn.tokens_used:,}", "text-emerald-400"
                )
                MthTurnUsageDialog._render_row(
                    "Cache Hit Ratio", cache_hit_str, "text-emerald-300"
                )
                MthTurnUsageDialog._render_row(
                    "Uncached Input", f"{turn.uncached_input_tokens:,}"
                )
                MthTurnUsageDialog._render_row(
                    "Cache Read", f"{turn.cache_read_tokens:,}"
                )
                MthTurnUsageDialog._render_row(
                    "Cache Write", f"{turn.cache_write_tokens:,}"
                )
                MthTurnUsageDialog._render_row(
                    "Output Tokens", f"{turn.output_tokens:,}"
                )
        dialog.open()

    @staticmethod
    def _render_row(label: str, value: str, value_cls: str = "text-slate-200") -> None:
        with ui.row().classes(
            "w-full justify-between items-center py-1 border-b border-[#1c202e]"
        ):
            ui.label(label).classes("text-slate-400")
            ui.label(value).classes(f"font-semibold {value_cls}")


class MthUserBubble(ui.column):
    """Right-aligned user prompt directive with clock and action toolbar."""

    def __init__(
        self,
        turn: MthTurnItem,
        on_copy: Callable[[str], Any] | None = None,
        on_fork: Callable[[str], Any] | None = None,
        on_edit: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.turn = turn
        self.on_copy = on_copy
        self.on_fork = on_fork
        self.on_edit = on_edit
        self.classes("w-full items-end gap-1.5 group")
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # Main prompt card
            with ui.card().classes(
                "bg-[#1c202e] border border-[#2c3345] text-slate-100 px-4 py-2.5 rounded-2xl rounded-tr-sm max-w-[85%] text-sm shadow-md"
            ):
                ui.label(self.turn.user_text).classes(
                    "leading-relaxed whitespace-pre-wrap"
                )

            # Action Toolbar below bubble (Timestamp, Copy, Fork, Edit)
            with ui.row().classes(
                "items-center gap-1 text-[11px] font-mono text-slate-500 opacity-60 group-hover:opacity-100 transition-opacity pr-1"
            ):
                clock_text = format_clock_time(self.turn.created_at)
                if clock_text:
                    ui.label(clock_text).classes("mr-1 text-[10px]")

                # Copy action
                btn_copy = (
                    ui.button(icon="content_copy", on_click=self._handle_copy)
                    .props("dense flat round size=xs")
                    .classes("text-slate-400 hover:text-white")
                )
                with btn_copy:
                    ui.tooltip("Copy prompt").classes("text-xs")

                # Fork action
                if self.on_fork:
                    btn_fork = (
                        ui.button(
                            icon="fork_right",
                            on_click=self._handle_fork,
                        )
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with btn_fork:
                        ui.tooltip("Fork session at this turn").classes("text-xs")

                # Edit prompt action
                if self.on_edit:
                    btn_edit = (
                        ui.button(
                            icon="edit",
                            on_click=self._handle_edit,
                        )
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with btn_edit:
                        ui.tooltip("Edit prompt in composer").classes("text-xs")

    def _handle_copy(self) -> None:
        try:
            if getattr(core, "loop", None) is not None:
                ui.run_javascript(
                    f"navigator.clipboard.writeText({repr(self.turn.user_text)})"
                )
                ui.notify(
                    "Prompt copied to clipboard",
                    type="positive",
                    position="top",
                    timeout=1200,
                )
        except Exception:
            pass
        if self.on_copy:
            self.on_copy(self.turn.user_text)

    def _handle_fork(self) -> None:
        if self.on_fork:
            self.on_fork(self.turn.turn_id)

    def _handle_edit(self) -> None:
        if self.on_edit:
            self.on_edit(self.turn.user_text)


class MthReasoningRow(ui.expansion):
    """Assistant deliberation fold with live preview and duration tracking."""

    def __init__(self, initial_thought: str = "", is_running: bool = False) -> None:
        super().__init__("Thinking", icon="psychology")
        self.start_time = time.time() if is_running else None
        self.is_running = is_running
        self.thoughts: list[str] = [initial_thought] if initial_thought else []

        self.classes(
            "w-full text-xs text-amber-400 bg-[#11131a] border border-[#232736] rounded-lg transition-all"
        )
        self._build_header_and_body()

    def _build_header_and_body(self) -> None:
        with self:
            with ui.row().classes(
                "w-full items-center justify-between pb-1 text-slate-400"
            ):
                with ui.row().classes("items-center gap-1.5 overflow-hidden flex-grow"):
                    self.status_dot = ui.element("div").classes(
                        f"w-2 h-2 rounded-full {'bg-amber-400 animate-pulse' if self.is_running else 'bg-amber-600'} shrink-0"
                    )
                    self.preview_label = ui.label("").classes(
                        "text-[11px] text-slate-400 italic truncate max-w-[70%]"
                    )
                with ui.row().classes("items-center gap-1 shrink-0"):
                    self.duration_badge = ui.badge("0.0s", color="amber-9").classes(
                        "font-mono text-[10px]"
                    )
                    btn_copy = (
                        ui.button(icon="content_copy", on_click=self._handle_copy)
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with btn_copy:
                        ui.tooltip("Copy deliberation").classes("text-xs")

            # Monospaced full deliberation body
            self.body_label = ui.label("").classes(
                "font-mono text-xs text-slate-300 p-2 whitespace-pre-wrap leading-relaxed bg-[#0c0d12] rounded border border-[#1e2230]"
            )
        self._refresh()

    def append_thought(self, text: str) -> None:
        """Append thought delta to deliberation."""
        self.thoughts.append(text)
        self._refresh()

    def set_running(self, running: bool) -> None:
        """Update active thinking state and finalize duration."""
        self.is_running = running
        if not running and self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.duration_badge.set_text(f"{elapsed:.1f}s")
            self.status_dot.classes(
                replace="w-2 h-2 rounded-full bg-amber-600 shrink-0"
            )
        elif running:
            self.start_time = time.time()
            self.status_dot.classes(
                replace="w-2 h-2 rounded-full bg-amber-400 animate-pulse shrink-0"
            )
        self._refresh()

    def _refresh(self) -> None:
        full_text = "\n".join(self.thoughts)
        self.body_label.set_text(full_text)
        first_line = clean_first_line(full_text)
        self.preview_label.set_text(first_line)
        if self.is_running and self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.duration_badge.set_text(f"{elapsed:.1f}s")

    def _handle_copy(self) -> None:
        full_text = "\n".join(self.thoughts)
        try:
            if getattr(core, "loop", None) is not None:
                ui.run_javascript(f"navigator.clipboard.writeText({repr(full_text)})")
                ui.notify(
                    "Reasoning copied to clipboard",
                    type="positive",
                    position="top",
                    timeout=1200,
                )
        except Exception:
            pass


class MthAssistantBubble(ui.column):
    """Assistant output prose container with code highlighting and actions toolbar."""

    def __init__(
        self,
        turn: MthTurnItem,
        on_copy: Callable[[str], Any] | None = None,
        on_fork: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.turn = turn
        self.on_copy = on_copy
        self.on_fork = on_fork
        self.classes("w-full gap-1 group")
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # Markdown prose
            self.markdown = ui.markdown(
                self.turn.assistant_text,
                extras=["fenced-code-blocks", "tables"],
            ).classes("w-full text-sm leading-relaxed text-slate-200")

            # Assistant Action Toolbar
            with ui.row().classes(
                "items-center gap-2 text-[11px] font-mono text-slate-500 opacity-60 group-hover:opacity-100 transition-opacity pt-1 pl-1"
            ):
                clock_text = format_clock_time(self.turn.created_at)
                if clock_text:
                    ui.label(clock_text).classes("text-[10px]")

                # Copy assistant prose
                btn_copy = (
                    ui.button(icon="content_copy", on_click=self._handle_copy)
                    .props("dense flat round size=xs")
                    .classes("text-slate-400 hover:text-white")
                )
                with btn_copy:
                    ui.tooltip("Copy response").classes("text-xs")

                # Fork session at this turn
                if self.on_fork:
                    btn_fork = (
                        ui.button(
                            icon="fork_right",
                            on_click=self._handle_fork,
                        )
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with btn_fork:
                        ui.tooltip("Fork session at this turn").classes("text-xs")

                # Turn Token Usage Pill
                if self.turn.tokens_used > 0:
                    with (
                        ui.button(on_click=lambda: MthTurnUsageDialog.show(self.turn))
                        .props("dense flat no-caps size=xs")
                        .classes(
                            "text-[10px] font-mono text-emerald-400 hover:text-emerald-300 bg-[#161922] px-2 py-0.5 rounded border border-[#232736]"
                        )
                    ):
                        ui.icon("storage", size="12px").classes("mr-1")
                        ui.label(f"{self.turn.tokens_used:,} tok")

    def set_content(self, text: str) -> None:
        """Update markdown content."""
        self.turn.assistant_text = text
        self.markdown.set_content(text)

    def _handle_fork(self) -> None:
        if self.on_fork:
            self.on_fork(self.turn.turn_id)

    def _handle_copy(self) -> None:
        try:
            if getattr(core, "loop", None) is not None:
                ui.run_javascript(
                    f"navigator.clipboard.writeText({repr(self.turn.assistant_text)})"
                )
                ui.notify(
                    "Response copied to clipboard",
                    type="positive",
                    position="top",
                    timeout=1200,
                )
        except Exception:
            pass
        if self.on_copy:
            self.on_copy(self.turn.assistant_text)


class MthCompactionItem(ui.row):
    """Expandable fold marking historical turns folded into a summary checkpoint."""

    def __init__(
        self, summary: str, folded_count: int = 0, tokens_saved: int = 0
    ) -> None:
        super().__init__()
        self.summary = summary
        self.folded_count = folded_count
        self.tokens_saved = tokens_saved
        self.classes("w-full items-center justify-center my-3")
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            with ui.expansion("Context Compaction", icon="compress").classes(
                "w-full max-w-2xl text-xs text-blue-400 bg-[#11131a] border border-[#232736] rounded-xl shadow-sm"
            ):
                with ui.row().classes(
                    "w-full items-center justify-between pb-1 text-slate-400 text-[11px] font-mono"
                ):
                    if self.folded_count > 0:
                        ui.label(
                            f"Folded {self.folded_count} turns into durable checkpoint"
                        )
                    if self.tokens_saved > 0:
                        ui.badge(
                            f"Saved {self.tokens_saved:,} tokens", color="blue-9"
                        ).classes("text-[10px]")

                ui.markdown(self.summary).classes(
                    "font-mono text-xs text-slate-300 p-2 whitespace-pre-wrap"
                )


class MthRunningTail(ui.row):
    """Live streaming status tail with elapsed stopwatch timer."""

    def __init__(self, status_label: str = "Thinking...") -> None:
        super().__init__()
        self.status_label = status_label
        self.start_time = time.time()
        self.classes("w-full items-center gap-2 py-3 select-none")
        self._build_ui()

    def _build_ui(self) -> None:
        self.clear()
        with self:
            ui.element("div").classes("flex-grow border-b border-[#232736]/60")
            with ui.row().classes(
                "items-center gap-2 bg-[#161922] border border-[#262b3a] rounded-full px-3 py-1 shadow-md"
            ):
                # Pulsing tail dot
                ui.element("div").classes(
                    "w-2 h-2 rounded-full bg-blue-500 animate-pulse"
                )
                self.label = ui.label(self.status_label).classes(
                    "font-mono text-xs text-blue-300 font-medium"
                )
                self.timer_label = ui.label("0.0s").classes(
                    "font-mono text-[10px] text-slate-400"
                )
            ui.element("div").classes("flex-grow border-b border-[#232736]/60")

    def update_label(self, label: str) -> None:
        """Update current status text."""
        self.status_label = label
        self.label.set_text(label)

    def tick(self) -> None:
        """Update elapsed timer reading."""
        elapsed = time.time() - self.start_time
        self.timer_label.set_text(f"{elapsed:.1f}s")


class MthTurnNavigator(ui.column):
    """Vertical mini-rail allowing direct jumping to discrete conversation turns."""

    def __init__(self, on_jump_to_turn: Callable[[str], Any] | None = None) -> None:
        super().__init__()
        self.on_jump_to_turn = on_jump_to_turn
        self.classes(
            "absolute left-2 top-8 z-20 flex flex-col gap-1.5 p-1 bg-[#11131a]/80 backdrop-blur-md border border-[#232736]/60 rounded-full"
        )
        self.turn_marks: list[tuple[str, str]] = []  # (turn_id, summary)

    def add_turn_mark(self, turn_id: str, summary: str, on_click_callback: Any) -> None:
        """Add a clickable turn mark pill into the rail."""
        self.turn_marks.append((turn_id, summary))
        with self:
            btn = (
                ui.button(on_click=on_click_callback)
                .props("dense round flat size=xs")
                .classes(
                    "w-6 h-6 text-[10px] font-mono text-slate-400 hover:text-white hover:bg-[#232736] rounded-full"
                )
            )
            with btn:
                ui.label(str(len(self.turn_marks)))
                ui.tooltip(f"Turn {len(self.turn_marks)}: {summary[:40]}...").classes(
                    "text-xs"
                )


class MthTimeline(ui.element):
    """The chronological stream of conversation turns displaying directives, deliberation, and tools."""

    def __init__(
        self,
        on_fork_turn: Callable[[str], Any] | None = None,
        on_edit_prompt: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__("div")
        self.on_fork_turn = on_fork_turn
        self.on_edit_prompt = on_edit_prompt
        self.classes("w-full flex-grow relative overflow-hidden flex flex-col")

        self.rendered_turns: dict[str, MthTurnItem] = {}
        self._turn_containers: dict[str, ui.column] = {}
        self._reasoning_rows: dict[str, MthReasoningRow] = {}
        self._assistant_bubbles: dict[str, MthAssistantBubble] = {}
        self.running_tail: MthRunningTail | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # 1. Turn Navigator Rail
            self.navigator = MthTurnNavigator()

            # 2. Main Scroll Area
            self.scroll_area = ui.scroll_area().classes("w-full h-full px-8 py-6")
            with self.scroll_area:
                self.content_column = ui.column().classes(
                    "w-full max-w-3xl mx-auto gap-6 pb-20"
                )

            # 3. Floating "Scroll to Bottom" Button
            self.to_bottom_btn = (
                ui.button(icon="keyboard_arrow_down", on_click=self.scroll_to_bottom)
                .props("dense round unelevated color=primary")
                .classes(
                    "absolute right-6 bottom-4 z-20 shadow-lg text-white hover:scale-105 transition-transform"
                )
            )

    def scroll_to_bottom(self) -> None:
        """Smoothly scroll to the bottom of the timeline."""
        self.scroll_area.scroll_to(percent=1.0)

    def scroll_to_turn(self, turn_id: str) -> None:
        """Scroll to a specific turn container."""
        if turn_id in self._turn_containers:
            container = self._turn_containers[turn_id]
            container.run_method("scrollIntoView", {"behavior": "smooth"})

    def render_turn(self, turn: MthTurnItem) -> None:
        """Render a turn card into the timeline and register in navigator."""
        self.rendered_turns[turn.turn_id] = turn

        with self.content_column:
            # If turn represents a compaction checkpoint, render compaction item first
            if turn.is_compacted and turn.compaction_summary:
                MthCompactionItem(
                    summary=turn.compaction_summary,
                    folded_count=turn.compaction_folded_count,
                    tokens_saved=turn.tokens_used,
                )

            turn_box = ui.column().classes("w-full gap-3")
            self._turn_containers[turn.turn_id] = turn_box

            with turn_box:
                # 1. User directive bubble with actions
                MthUserBubble(
                    turn=turn,
                    on_fork=self.on_fork_turn,
                    on_edit=self.on_edit_prompt,
                )

                # 2. Deliberation expansion fold with live preview & duration
                reasoning_text = "\n".join(turn.reasoning) if turn.reasoning else ""
                reasoning_row = MthReasoningRow(
                    initial_thought=reasoning_text,
                    is_running=turn.is_deliberating,
                )
                self._reasoning_rows[turn.turn_id] = reasoning_row

                # 3. Tool Cards container
                tools_box = ui.column().classes("w-full gap-2")
                for tool in turn.tool_calls:
                    with tools_box:
                        create_tool_card(tool)

                # 4. Assistant Markdown prose with action toolbar
                assistant_bubble = MthAssistantBubble(
                    turn=turn,
                    on_fork=self.on_fork_turn,
                )
                self._assistant_bubbles[turn.turn_id] = assistant_bubble

        # Register in Turn Navigator
        self.navigator.add_turn_mark(
            turn.turn_id,
            turn.user_text,
            lambda _, tid=turn.turn_id: self.scroll_to_turn(tid),
        )

        self.scroll_to_bottom()

    def start_running_tail(self, status_label: str = "Thinking...") -> None:
        """Show active running status tail."""
        self.stop_running_tail()
        with self.content_column:
            self.running_tail = MthRunningTail(status_label=status_label)
        self.scroll_to_bottom()

    def stop_running_tail(self) -> None:
        """Dismiss active running status tail."""
        if self.running_tail:
            self.running_tail.delete()
            self.running_tail = None

    def append_reasoning(self, turn_id: str, thought: str) -> None:
        """Append a thought fragment to a turn's deliberation fold."""
        if turn_id in self.rendered_turns:
            self.rendered_turns[turn_id].reasoning.append(thought)
            if turn_id in self._reasoning_rows:
                self._reasoning_rows[turn_id].append_thought(thought)
                self.scroll_to_bottom()

    def set_reasoning_running(self, turn_id: str, running: bool) -> None:
        """Toggle running status on a turn's deliberation fold."""
        if turn_id in self._reasoning_rows:
            self._reasoning_rows[turn_id].set_running(running)

    def append_assistant_text(self, turn_id: str, text: str) -> None:
        """Append streaming token text to the assistant message."""
        if turn_id in self.rendered_turns:
            self.rendered_turns[turn_id].assistant_text += text
            if turn_id in self._assistant_bubbles:
                self._assistant_bubbles[turn_id].set_content(
                    self.rendered_turns[turn_id].assistant_text
                )
                self.scroll_to_bottom()
