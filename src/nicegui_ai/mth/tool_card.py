"""Specialized Tool Card components matching the reference harness interface."""

import json
from collections.abc import Callable
from typing import Any

from nicegui import ui

from .state import MthToolCallItem, ToolExecutionStatus


class MthToolCard(ui.card):
    """Base visual card presenting tool execution lifecycle, parameters, and approval gates."""

    def __init__(
        self,
        tool_item: MthToolCallItem,
        on_approve: Callable[[str], Any] | None = None,
        on_veto: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.tool_item = tool_item
        self.on_approve = on_approve
        self.on_veto = on_veto

        self.classes(
            "w-full bg-[#11131a] border border-[#232736] rounded-lg p-3 my-2 shadow-sm text-sm"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # Header row: Tool name, status badge
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("terminal", size="xs").classes("text-[#3b82f6]")
                    ui.label(self.tool_item.name).classes(
                        "font-mono font-semibold text-slate-200"
                    )

                self.status_badge = ui.badge(
                    self.tool_item.status.value.replace("_", " ").title(),
                    color=self._get_status_color(),
                ).classes("text-xs uppercase font-mono")

            # Collapsible arguments fold
            with ui.expansion("Arguments", icon="code").classes(
                "w-full text-xs text-slate-400 mt-1"
            ):
                args_text = json.dumps(self.tool_item.args, indent=2)
                ui.code(args_text, language="json").classes(
                    "w-full bg-[#090a0f] text-xs font-mono rounded"
                )

            # Approval Gate Controls
            self.approval_container = ui.row().classes(
                "w-full items-center justify-end gap-2 mt-2"
            )
            self._render_approval_controls()

            # Result or Error container
            self.output_container = ui.column().classes("w-full mt-2")
            self._render_output()

    def _get_status_color(self) -> str:
        match self.tool_item.status:
            case ToolExecutionStatus.PENDING:
                return "grey-7"
            case ToolExecutionStatus.AWAITING_APPROVAL:
                return "amber-8"
            case ToolExecutionStatus.EXECUTING:
                return "blue-7"
            case ToolExecutionStatus.COMPLETED:
                return "emerald-7"
            case ToolExecutionStatus.FAILED:
                return "rose-7"

    def _render_approval_controls(self) -> None:
        self.approval_container.clear()
        if (
            self.tool_item.approval_required
            and self.tool_item.status == ToolExecutionStatus.AWAITING_APPROVAL
        ):
            with self.approval_container:
                ui.label("Authorization required:").classes(
                    "text-xs text-amber-400 mr-auto font-mono"
                )
                ui.button("Approve", on_click=self.approve, color="positive").props(
                    "dense no-caps size=sm"
                )
                ui.button("Veto", on_click=self.veto, color="negative").props(
                    "dense no-caps flat size=sm"
                )

    def _render_output(self) -> None:
        self.output_container.clear()
        if self.tool_item.result:
            with self.output_container:
                ui.label("Result:").classes("text-xs text-slate-400 font-mono")
                ui.code(self.tool_item.result).classes(
                    "w-full bg-[#090a0f] text-xs font-mono rounded p-2"
                )
        elif self.tool_item.error:
            with self.output_container:
                ui.label("Error:").classes("text-xs text-rose-400 font-mono")
                ui.code(self.tool_item.error).classes(
                    "w-full bg-[#1e1014] text-rose-300 text-xs font-mono rounded p-2"
                )

    def approve(self) -> None:
        """Trigger tool approval."""
        self.tool_item.approved = True
        self.tool_item.status = ToolExecutionStatus.EXECUTING
        self.status_badge.set_text("Executing")
        self.status_badge.props(f"color={self._get_status_color()}")
        self._render_approval_controls()
        if self.on_approve:
            self.on_approve(self.tool_item.call_id)

    def veto(self) -> None:
        """Trigger tool veto."""
        self.tool_item.approved = False
        self.tool_item.status = ToolExecutionStatus.FAILED
        self.tool_item.error = "Execution vetoed by user"
        self.status_badge.set_text("Failed")
        self.status_badge.props(f"color={self._get_status_color()}")
        self._render_approval_controls()
        self._render_output()
        if self.on_veto:
            self.on_veto(self.tool_item.call_id)

    def complete(self, result: str) -> None:
        """Mark tool call complete with output."""
        self.tool_item.status = ToolExecutionStatus.COMPLETED
        self.tool_item.result = result
        self.status_badge.set_text("Completed")
        self.status_badge.props(f"color={self._get_status_color()}")
        self._render_approval_controls()
        self._render_output()

    def fail(self, error: str) -> None:
        """Mark tool call failed with error message."""
        self.tool_item.status = ToolExecutionStatus.FAILED
        self.tool_item.error = error
        self.status_badge.set_text("Failed")
        self.status_badge.props(f"color={self._get_status_color()}")
        self._render_approval_controls()
        self._render_output()


class BashToolCard(MthToolCard):
    """Specialized tool card rendering terminal command execution with stdout/stderr."""

    def __init__(
        self,
        tool_item: MthToolCallItem,
        on_approve: Callable[[str], Any] | None = None,
        on_veto: Callable[[str], Any] | None = None,
    ) -> None:
        self.command = str(tool_item.args.get("command", ""))
        self.cwd = str(tool_item.args.get("cwd", ""))
        self.exit_code: int | None = None
        super().__init__(tool_item, on_approve=on_approve, on_veto=on_veto)

    def _build_ui(self) -> None:
        with self:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("terminal", size="xs").classes("text-[#3b82f6]")
                    ui.label("$ " + self.command).classes(
                        "font-mono font-semibold text-slate-200 truncate max-w-md"
                    )
                self.status_badge = ui.badge(
                    self.tool_item.status.value.replace("_", " ").title(),
                    color=self._get_status_color(),
                ).classes("text-xs uppercase font-mono")

            if self.cwd:
                ui.label(f"cwd: {self.cwd}").classes(
                    "text-[11px] text-slate-500 font-mono mt-0.5"
                )

            self.approval_container = ui.row().classes(
                "w-full items-center justify-end gap-2 mt-2"
            )
            self._render_approval_controls()

            self.output_container = ui.column().classes("w-full mt-2")
            self._render_output()

    def set_output(self, output: str, exit_code: int = 0) -> None:
        """Update terminal output and exit code."""
        self.exit_code = exit_code
        if exit_code == 0:
            self.complete(output)
        else:
            self.fail(output)


class FileMutationToolCard(MthToolCard):
    """Specialized tool card displaying file edits and code diffs."""

    def __init__(
        self,
        tool_item: MthToolCallItem,
        on_approve: Callable[[str], Any] | None = None,
        on_veto: Callable[[str], Any] | None = None,
    ) -> None:
        self.file_path = str(
            tool_item.args.get("path")
            or tool_item.args.get("file_path")
            or "unnamed_file"
        )
        self.diff_content = str(
            tool_item.args.get("diff") or tool_item.args.get("new_string") or ""
        )
        super().__init__(tool_item, on_approve=on_approve, on_veto=on_veto)

    def _build_ui(self) -> None:
        with self:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("description", size="xs").classes("text-[#8b5cf6]")
                    ui.label(self.file_path).classes(
                        "font-mono font-semibold text-slate-200 truncate"
                    )
                self.status_badge = ui.badge(
                    self.tool_item.status.value.replace("_", " ").title(),
                    color=self._get_status_color(),
                ).classes("text-xs uppercase font-mono")

            if self.diff_content:
                with ui.expansion("View Diff", icon="difference").classes(
                    "w-full text-xs text-slate-400 mt-2"
                ):
                    ui.code(self.diff_content, language="diff").classes(
                        "w-full bg-[#090a0f] text-xs font-mono rounded"
                    )

            self.approval_container = ui.row().classes(
                "w-full items-center justify-end gap-2 mt-2"
            )
            self._render_approval_controls()

            self.output_container = ui.column().classes("w-full mt-2")
            self._render_output()


class AskQuestionToolCard(MthToolCard):
    """Specialized card presenting interactive user questions, choices, and inputs."""

    def __init__(
        self,
        tool_item: MthToolCallItem,
        on_answer: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        self.question_text = str(tool_item.args.get("question", ""))
        self.options = list(tool_item.args.get("options", []))
        self.on_answer = on_answer
        self.selected_options: list[str] = []
        super().__init__(tool_item)

    def _build_ui(self) -> None:
        with self:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("help_outline", size="xs").classes("text-[#f59e0b]")
                    ui.label("Clarification Request").classes(
                        "font-sans font-semibold text-amber-400 text-xs uppercase"
                    )
                self.status_badge = ui.badge(
                    self.tool_item.status.value.replace("_", " ").title(),
                    color=self._get_status_color(),
                ).classes("text-xs uppercase font-mono")

            ui.label(self.question_text).classes(
                "text-sm text-slate-100 font-medium my-2"
            )

            # Options
            if self.options:
                with ui.column().classes("w-full gap-1 pl-2 mb-2"):
                    for opt in self.options:
                        ui.checkbox(
                            opt,
                            on_change=lambda e, o=opt: self._handle_toggle(o, e.value),
                        ).props("dense size=sm").classes("text-xs text-slate-300")

            # Custom answer input
            self.custom_input = (
                ui.input(placeholder="Custom clarification (optional)")
                .props("dense borderless")
                .classes(
                    "w-full bg-[#090a0f] text-xs font-sans rounded px-2 py-1 text-slate-200"
                )
            )

            with ui.row().classes("w-full justify-end mt-2"):
                ui.button(
                    "Submit Answer",
                    on_click=lambda: self.submit_answer(
                        selected=self.selected_options,
                        custom=self.custom_input.value or "",
                    ),
                    color="primary",
                ).props("dense no-caps size=sm")

            self.approval_container = ui.row().classes(
                "w-full items-center justify-end gap-2 mt-2"
            )
            self.output_container = ui.column().classes("w-full mt-2")

    def _handle_toggle(self, option: str, checked: bool) -> None:
        if checked and option not in self.selected_options:
            self.selected_options.append(option)
        elif not checked and option in self.selected_options:
            self.selected_options.remove(option)

    def submit_answer(self, selected: list[str], custom: str = "") -> None:
        """Submit the selected answer back to the agent loop."""
        answer_payload = {"selected": selected, "custom": custom}
        self.complete(json.dumps(answer_payload))
        if self.on_answer:
            self.on_answer(answer_payload)


class ReadToolCard(MthToolCard):
    """Specialized card for read-only inspection tools (read_file, list_directory, search)."""

    def __init__(
        self,
        tool_item: MthToolCallItem,
        on_approve: Callable[[str], Any] | None = None,
        on_veto: Callable[[str], Any] | None = None,
    ) -> None:
        self.target_path = str(
            tool_item.args.get("path")
            or tool_item.args.get("file_path")
            or tool_item.args.get("directory")
            or tool_item.args.get("query")
            or ""
        )
        super().__init__(tool_item, on_approve=on_approve, on_veto=on_veto)

    def _build_ui(self) -> None:
        with self:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("visibility", size="xs").classes("text-[#06b6d4]")
                    ui.label(f"{self.tool_item.name}: {self.target_path}").classes(
                        "font-mono font-semibold text-slate-200 truncate max-w-md"
                    )
                self.status_badge = ui.badge(
                    self.tool_item.status.value.replace("_", " ").title(),
                    color=self._get_status_color(),
                ).classes("text-xs uppercase font-mono")

            self.approval_container = ui.row().classes(
                "w-full items-center justify-end gap-2 mt-2"
            )
            self._render_approval_controls()

            self.output_container = ui.column().classes("w-full mt-2")
            self._render_output()


class MthApprovalPanel(ui.card):
    """Composer takeover and inline approval flow matching reference ApprovalPanel.tsx."""

    def __init__(
        self,
        call_id: str,
        tool_name: str,
        reason: str | None = None,
        command_detail: str | None = None,
        on_allow: Callable[[str], Any] | None = None,
        on_reject: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.call_id = call_id
        self.tool_name = tool_name
        self.reason = reason or f"Authorization required for {tool_name}"
        self.command_detail = command_detail
        self.on_allow = on_allow
        self.on_reject = on_reject
        self.answered = False

        self.classes(
            "w-full bg-[#181512] border border-amber-600/40 rounded-xl p-3 shadow-lg flex flex-col gap-2.5 my-2"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # 1. Strip with StateDot and waiting label
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    self.dot = ui.element("div").classes(
                        "w-2 h-2 rounded-full "
                        + (
                            "bg-blue-400 animate-pulse"
                            if self.answered
                            else "bg-amber-400 animate-pulse"
                        )
                    )
                    self.strip_label = ui.label(
                        "Answered" if self.answered else "Waiting for approval"
                    ).classes(
                        "text-xs font-mono font-semibold text-amber-300 uppercase tracking-wide"
                    )

                ui.badge(self.tool_name, color="amber-9").classes(
                    "font-mono text-[10px]"
                )

            # 2. Headline reason
            ui.label(self.reason).classes("text-xs font-medium text-slate-200")

            # 3. Command detail preview (if provided)
            if self.command_detail:
                ui.code(self.command_detail).classes(
                    "w-full bg-[#0d0c0a] text-xs font-mono text-amber-200/90 rounded p-2 overflow-x-auto"
                )

            # 4. Action Row
            self.action_row = ui.row().classes(
                "w-full items-center justify-end gap-2 pt-1"
            )
            with self.action_row:
                self.reject_btn = (
                    ui.button(
                        "Reject",
                        on_click=self.reject,
                        color="negative",
                    )
                    .props("dense no-caps flat size=sm")
                    .classes("text-rose-400 hover:bg-rose-500/10 px-3")
                )

                self.allow_btn = (
                    ui.button(
                        "Allow Once",
                        on_click=self.allow,
                        color="positive",
                    )
                    .props("dense no-caps unelevated size=sm")
                    .classes("bg-blue-600 hover:bg-blue-500 text-white px-3")
                )

    def allow(self) -> None:
        """Trigger one-time authorization for the pending tool execution."""
        if self.answered:
            return
        self.answered = True
        self.strip_label.text = "Allowed"
        self.dot.classes(remove="bg-amber-400 animate-pulse", add="bg-emerald-400")
        self.reject_btn.disable()
        self.allow_btn.disable()
        if self.on_allow:
            self.on_allow(self.call_id)

    def reject(self) -> None:
        """Veto execution of the pending tool."""
        if self.answered:
            return
        self.answered = True
        self.strip_label.text = "Rejected"
        self.dot.classes(remove="bg-amber-400 animate-pulse", add="bg-rose-400")
        self.reject_btn.disable()
        self.allow_btn.disable()
        if self.on_reject:
            self.on_reject(self.call_id)


def create_tool_card(
    tool: MthToolCallItem,
    on_approve: Callable[[str], Any] | None = None,
    on_veto: Callable[[str], Any] | None = None,
) -> MthToolCard:
    """Factory creating specialized or generic MthToolCard based on tool signature."""
    name = tool.name.lower()
    if name in ("bash", "run_command", "shell"):
        return BashToolCard(tool_item=tool, on_approve=on_approve, on_veto=on_veto)
    if name in ("edit_file", "write_file", "apply_diff"):
        return FileMutationToolCard(
            tool_item=tool, on_approve=on_approve, on_veto=on_veto
        )
    if name in ("ask_question", "confirm", "prompt_user"):
        return AskQuestionToolCard(tool_item=tool)
    if name in ("read_file", "list_directory", "search", "search_web"):
        return ReadToolCard(tool_item=tool, on_approve=on_approve, on_veto=on_veto)
    return MthToolCard(tool_item=tool, on_approve=on_approve, on_veto=on_veto)
