"""Anchored Composer dock with multi-state action button, stats pills, and slash command fastpicker."""

import uuid
from collections.abc import Callable
from typing import Any

from nicegui import ui

from .command_picker import MthCommandFastpicker
from .context_meter import MthContextMeter
from .state import (
    MthAttachment,
    MthCommandItem,
    MthContextOccupancy,
    MthSessionStats,
    format_tokens,
)
from .stats_pills import MthStatsPills


class MthModelSelectDialog(ui.dialog):
    """Searchable dialog for selecting LLM model and reasoning effort."""

    def __init__(
        self,
        current_model: str,
        available_models: list[str],
        reasoning_effort: str = "medium",
        on_select: Callable[[str, str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.selected_model = current_model
        self.available_models = available_models
        self.reasoning_effort = reasoning_effort
        self.on_select = on_select
        self.search_query = ""
        self._build_ui()

    def _build_ui(self) -> None:
        with (
            self,
            ui.card().classes(
                "w-[420px] bg-[#141722] border border-[#262c3d] p-4 rounded-2xl shadow-2xl flex flex-col gap-3 text-slate-100"
            ),
        ):
            # Header
            with ui.row().classes(
                "w-full items-center justify-between pb-1 border-b border-[#232736]"
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("tune", size="18px").classes("text-blue-400")
                    ui.label("Model & Deliberation").classes(
                        "text-sm font-semibold text-white"
                    )
                ui.button(
                    icon="close",
                    on_click=self.close,
                ).props("dense flat round size=xs").classes(
                    "text-slate-400 hover:text-white"
                )

            # Search bar
            with ui.row().classes(
                "w-full items-center gap-2 bg-[#1a1f2c] px-2.5 py-1.5 rounded-lg border border-[#2b3345]"
            ):
                ui.icon("search", size="16px").classes("text-slate-400")
                self.search_input = (
                    ui.input(placeholder="Search models...")
                    .props("dense borderless autofocus")
                    .classes(
                        "flex-grow text-xs text-white placeholder:text-slate-500 font-sans"
                    )
                )
                self.search_input.on("input", self._on_search)

            # Reasoning Effort Toggle Row
            with ui.row().classes("w-full items-center justify-between py-1 px-1"):
                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("psychology", size="16px").classes("text-purple-400")
                    ui.label("Reasoning Effort").classes(
                        "text-xs text-slate-300 font-medium"
                    )

                self.effort_btn_group = ui.row().classes(
                    "items-center gap-1 bg-[#1a1f2c] p-0.5 rounded-lg border border-[#2b3345]"
                )
                with self.effort_btn_group:
                    for eff in ["low", "medium", "high"]:
                        is_active = eff == self.reasoning_effort
                        active_cls = (
                            "bg-blue-600 text-white"
                            if is_active
                            else "text-slate-400 hover:text-white"
                        )
                        ui.button(
                            eff.capitalize(),
                            on_click=lambda _, e=eff: self._set_effort(e),
                        ).props("dense flat no-caps size=xs").classes(
                            f"px-2 py-0.5 rounded text-[11px] font-sans font-medium transition-colors {active_cls}"
                        )

            # Model options list
            self.model_list_container = ui.column().classes(
                "w-full gap-1 max-h-[220px] overflow-y-auto pr-1"
            )
            self._render_model_list()

            # Footer
            with ui.row().classes("w-full justify-end pt-2 border-t border-[#232736]"):
                ui.button("Done", on_click=self._confirm).props(
                    "dense unelevated size=sm"
                ).classes(
                    "bg-blue-600 hover:bg-blue-500 text-white px-4 rounded-lg font-medium"
                )

    def _on_search(self, e: Any) -> None:
        self.search_query = (self.search_input.value or "").strip().lower()
        self._render_model_list()

    def _set_effort(self, effort: str) -> None:
        self.reasoning_effort = effort
        self._build_ui()

    def _render_model_list(self) -> None:
        self.model_list_container.clear()
        filtered = [
            m
            for m in self.available_models
            if not self.search_query or self.search_query in m.lower()
        ]

        with self.model_list_container:
            for m in filtered:
                is_selected = m == self.selected_model
                with (
                    ui.row()
                    .classes(
                        "w-full items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors "
                        + (
                            "bg-blue-500/10 border border-blue-500/30"
                            if is_selected
                            else "hover:bg-[#1f2535]"
                        )
                    )
                    .on("click", lambda _, model_name=m: self._select_model(model_name))
                ):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("memory", size="16px").classes(
                            "text-blue-400" if is_selected else "text-slate-500"
                        )
                        ui.label(m).classes(
                            "font-mono text-xs "
                            + (
                                "text-white font-semibold"
                                if is_selected
                                else "text-slate-300"
                            )
                        )
                    if is_selected:
                        ui.icon("check", size="16px").classes("text-blue-400")

    def _select_model(self, model_name: str) -> None:
        self.selected_model = model_name
        self._render_model_list()

    def _confirm(self) -> None:
        self.close()
        if self.on_select:
            self.on_select(self.selected_model, self.reasoning_effort)


class MthComposer(ui.column):
    """The primary input dock for prompt authoring, cancellation, and slash commands."""

    def __init__(
        self,
        on_send: Callable[[str], Any] | None = None,
        on_abort: Callable[[], Any] | None = None,
        on_model_change: Callable[[str, str], Any] | None = None,
        on_permission_change: Callable[[str], Any] | None = None,
        on_plan_toggle: Callable[[bool], Any] | None = None,
        on_attachment_add: Callable[[MthAttachment], Any] | None = None,
        on_attachment_remove: Callable[[str], Any] | None = None,
        slash_commands: list[str] | None = None,
        placeholder: str = "Ask harness agent or type / for commands...",
        metrics: MthSessionStats | None = None,
        current_model: str = "default-chat",
        available_models: list[str] | None = None,
        permission_preset: str = "auto",
        context_occupancy: MthContextOccupancy | None = None,
    ) -> None:
        super().__init__()
        self.on_send = on_send
        self.on_abort = on_abort
        self.on_model_change = on_model_change
        self.on_permission_change = on_permission_change
        self.on_plan_toggle = on_plan_toggle
        self.on_attachment_add = on_attachment_add
        self.on_attachment_remove = on_attachment_remove

        self.slash_commands = slash_commands or [
            "/plan",
            "/goal",
            "/compact",
            "/permission",
            "/clear",
            "/export",
            "/help",
        ]
        self.is_running = False
        self.current_model = current_model
        self.available_models = available_models or [
            "default-chat",
            "reasoner-pro",
            "gpt-4o",
            "claude-3-5-sonnet",
        ]
        self.reasoning_effort = "medium"
        self.permission_preset = permission_preset
        self.plan_mode = False
        self.attachments: list[MthAttachment] = []
        self.context_occupancy = context_occupancy or MthContextOccupancy()

        self.classes(
            "w-full max-w-[840px] mx-auto flex flex-col items-center gap-1.5 px-4 pb-2"
        )
        self._build_ui(placeholder, metrics)

    def _build_ui(self, placeholder: str, metrics: MthSessionStats | None) -> None:
        with self:
            # 1. Main Capsule Card (border hairline, rounded-2xl, elevated dark)
            self.card = ui.card().classes(
                "w-full bg-[#12151e] border border-[#232736] p-3 rounded-2xl shadow-2xl flex flex-col gap-2 relative transition-all"
            )
            with self.card:
                # Attachments rail
                self.attachment_rail = ui.row().classes(
                    "w-full items-center gap-2 empty:hidden pb-1 flex-wrap"
                )
                self._render_attachments()

                # Textarea input surface with autogrow
                with ui.column().classes("w-full gap-1"):
                    self.input = (
                        ui.textarea(placeholder=placeholder)
                        .props("autogrow borderless dense")
                        .classes(
                            "w-full text-sm text-slate-100 placeholder:text-slate-500 font-sans min-h-[44px] max-h-[300px] leading-relaxed resize-none"
                        )
                        .on("input", self._handle_input_change)
                        .on("keydown.enter", self._handle_keydown)
                    )

                    # Ghost hint label for commands
                    self.hint_label = ui.label("").classes(
                        "text-[11px] font-mono text-slate-500 italic hidden px-1"
                    )

                # Slash command suggestions chip strip
                self.slash_container = ui.row().classes(
                    "w-full items-center gap-1.5 hidden pb-1 flex-wrap"
                )
                with self.slash_container:
                    ui.label("Commands:").classes(
                        "text-[10px] font-mono text-slate-500 uppercase tracking-wide"
                    )
                    for cmd in self.slash_commands:
                        ui.button(
                            cmd,
                            on_click=lambda _, c=cmd: self._select_slash_command(c),
                        ).props("dense flat no-caps size=xs").classes(
                            "font-mono text-[11px] text-blue-400 bg-[#161922] hover:bg-[#1f2430] border border-[#262b3a] rounded px-2"
                        )

                # Control Row: Left tools and Right actions
                with ui.row().classes("w-full items-center justify-between pt-1"):
                    # Left tools
                    with ui.row().classes("items-center gap-2"):
                        # Add (+) Button (28px circle)
                        self.add_btn = (
                            ui.button(
                                icon="add",
                                on_click=self._open_command_picker,
                            )
                            .props("dense flat round size=sm")
                            .classes(
                                "w-7 h-7 bg-[#1c202d] hover:bg-[#282e40] text-slate-300 hover:text-white"
                            )
                            .tooltip("Add / Commands (/)")
                        )

                        # Command Fastpicker trigger (/)
                        ui.button(
                            "/",
                            on_click=self._toggle_slash_commands,
                        ).props("dense flat round size=sm").classes(
                            "w-7 h-7 bg-[#1c202d] hover:bg-[#282e40] text-slate-400 hover:text-blue-400 font-mono font-bold text-xs"
                        ).tooltip("Slash Commands")

                        # Attach File Button (paperclip)
                        self.attach_btn = (
                            ui.button(
                                icon="attach_file",
                                on_click=self._handle_attach_click,
                            )
                            .props("dense flat round size=sm")
                            .classes(
                                "w-7 h-7 bg-[#1c202d] hover:bg-[#282e40] text-slate-400 hover:text-white"
                            )
                            .tooltip("Attach File")
                        )

                        # Permission Preset Selector Dropdown
                        self._build_permission_dropdown()

                        # Plan Mode Toggle Pill
                        self.plan_btn = (
                            ui.button(
                                "Plan",
                                icon="format_list_bulleted",
                                on_click=self._toggle_plan_mode,
                            )
                            .props("dense flat no-caps size=xs")
                            .classes(
                                "px-2.5 py-1 rounded-lg text-xs font-medium border border-[#262c3d] "
                                + (
                                    "bg-blue-600/20 text-blue-400 border-blue-500/30"
                                    if self.plan_mode
                                    else "text-slate-400 hover:text-white hover:bg-[#1a1f2c]"
                                )
                            )
                            .tooltip("Toggle Planning Mode")
                        )

                    # Right tools (Model selector, Stop, Primary Send button)
                    with ui.row().classes("items-center gap-2"):
                        # Model Selector Pill
                        self.model_btn = (
                            ui.button(
                                on_click=self._open_model_dialog,
                            )
                            .props("dense flat no-caps size=xs")
                            .classes(
                                "px-2.5 py-1 rounded-lg text-xs font-mono font-medium border border-[#262c3d] text-slate-300 hover:text-white hover:bg-[#1a1f2c] flex items-center gap-1.5"
                            )
                        )
                        self._update_model_btn_label()

                        # Dedicated Stop Button (shown during running)
                        self.stop_btn = (
                            ui.button(
                                icon="stop",
                                on_click=self.abort,
                                color="negative",
                            )
                            .props("dense round unelevated size=sm")
                            .classes("w-7 h-7 hidden")
                            .tooltip("Stop generation (Esc)")
                        )

                        # Primary Action Button (34px circle, #3964FE / #3b82f6)
                        self.action_btn = (
                            ui.button(
                                icon="arrow_upward",
                                on_click=self._handle_action_click,
                            )
                            .props("dense round unelevated")
                            .classes(
                                "w-[34px] h-[34px] bg-[#3b82f6] hover:bg-[#2563eb] text-white flex items-center justify-center transition-all shadow-md"
                            )
                            .tooltip("Send (Enter)")
                        )

            # 2. Dock Container (Stats pills + Context Occupancy meter)
            with ui.row().classes("w-full items-center justify-between px-1"):
                # Left: Session Stats Pills (Tokens, Speed, TTFT, Cache)
                self.stats_pills = MthStatsPills(metrics=metrics)

                # Right: Context Occupancy Meter
                self.context_meter = MthContextMeter(occupancy=self.context_occupancy)

    def _build_permission_dropdown(self) -> None:
        preset_labels = {
            "auto": "Auto",
            "workspace-write": "Workspace Write",
            "read-only": "Read-Only",
            "full-access": "Full Access",
        }
        current_label = preset_labels.get(self.permission_preset, "Auto")

        with (
            ui.button(
                current_label,
                icon="shield",
            )
            .props("dense flat no-caps size=xs")
            .classes(
                "px-2.5 py-1 rounded-lg text-xs font-medium border border-[#262c3d] text-slate-400 hover:text-white hover:bg-[#1a1f2c]"
            ) as self.perm_btn
        ):
            ui.icon("arrow_drop_down", size="14px").classes("ml-0.5 text-slate-500")
            with ui.menu().classes(
                "bg-[#141722] border border-[#262c3d] p-1 rounded-xl shadow-xl"
            ):
                for val, lbl in preset_labels.items():
                    ui.menu_item(
                        lbl,
                        on_click=lambda _, v=val: self._set_permission(v),
                    ).classes(
                        "text-xs text-slate-300 hover:bg-[#1f2535] px-3 py-1.5 rounded-lg"
                    )

    def _update_model_btn_label(self) -> None:
        self.model_btn.clear()
        with self.model_btn:
            with ui.row().classes("items-center gap-1"):
                ui.icon("memory", size="14px").classes("text-blue-400")
                ui.label(self.current_model).classes("text-xs font-mono text-slate-200")
                if self.reasoning_effort:
                    ui.label(self.reasoning_effort[:3].upper()).classes(
                        "text-[9px] font-mono bg-[#1f2535] text-purple-300 px-1 py-0.2 rounded"
                    )
                ui.icon("arrow_drop_down", size="14px").classes("text-slate-500")

    def _open_model_dialog(self) -> None:
        dialog = MthModelSelectDialog(
            current_model=self.current_model,
            available_models=self.available_models,
            reasoning_effort=self.reasoning_effort,
            on_select=self._handle_model_selected,
        )
        dialog.open()

    def _handle_model_selected(self, model: str, effort: str) -> None:
        self.current_model = model
        self.reasoning_effort = effort
        self._update_model_btn_label()
        if self.on_model_change:
            self.on_model_change(model, effort)

    def _set_permission(self, preset: str) -> None:
        self.permission_preset = preset
        preset_labels = {
            "auto": "Auto",
            "workspace-write": "Workspace Write",
            "read-only": "Read-Only",
            "full-access": "Full Access",
        }
        self.perm_btn.text = preset_labels.get(preset, preset)
        if self.on_permission_change:
            self.on_permission_change(preset)

    def _toggle_plan_mode(self) -> None:
        self.plan_mode = not self.plan_mode
        if self.plan_mode:
            self.plan_btn.classes(
                add="bg-blue-600/20 text-blue-400 border-blue-500/30",
                remove="text-slate-400 hover:text-white hover:bg-[#1a1f2c]",
            )
        else:
            self.plan_btn.classes(
                remove="bg-blue-600/20 text-blue-400 border-blue-500/30",
                add="text-slate-400 hover:text-white hover:bg-[#1a1f2c]",
            )
        if self.on_plan_toggle:
            self.on_plan_toggle(self.plan_mode)

    def _open_command_picker(self) -> None:
        fastpicker = MthCommandFastpicker(on_select=self._handle_command_picker_select)
        fastpicker.open()

    def _handle_command_picker_select(self, cmd: MthCommandItem) -> None:
        self.set_text(f"{cmd.token} ")
        self.input.run_method("focus")

    def _render_attachments(self) -> None:
        self.attachment_rail.clear()
        if not self.attachments:
            return

        with self.attachment_rail:
            for att in self.attachments:
                with ui.row().classes(
                    "items-center gap-1.5 bg-[#1a1f2c] border border-[#2b3345] px-2 py-1 rounded-lg text-xs"
                ):
                    if att.is_image:
                        ui.icon("image", size="14px").classes("text-blue-400")
                    else:
                        ui.icon("description", size="14px").classes("text-slate-400")
                    ui.label(att.name).classes(
                        "text-slate-200 font-sans truncate max-w-[140px]"
                    )
                    if att.size_bytes > 0:
                        ui.label(f"({format_tokens(att.size_bytes)}B)").classes(
                            "text-[10px] text-slate-500 font-mono"
                        )
                    ui.button(
                        icon="close",
                        on_click=lambda _, aid=att.id: self._remove_attachment(aid),
                    ).props("dense flat round size=xs").classes(
                        "text-slate-500 hover:text-red-400 ml-1"
                    )

    def add_attachment(
        self, name: str, size_bytes: int = 0, is_image: bool = False
    ) -> MthAttachment:
        """Add an attachment chip to the composer."""
        att = MthAttachment(
            id=str(uuid.uuid4())[:8],
            name=name,
            size_bytes=size_bytes,
            is_image=is_image,
        )
        self.attachments.append(att)
        self._render_attachments()
        if self.on_attachment_add:
            self.on_attachment_add(att)
        return att

    def _remove_attachment(self, attachment_id: str) -> None:
        for att in list(self.attachments):
            if att.id == attachment_id:
                self.attachments.remove(att)
                break
        self._render_attachments()
        if self.on_attachment_remove:
            self.on_attachment_remove(attachment_id)

    def _handle_attach_click(self) -> None:
        # Prompt user or add sample attachment
        self.add_attachment(
            name="workspace-context.txt", size_bytes=1024, is_image=False
        )

    def _toggle_slash_commands(self) -> None:
        """Toggle visibility of slash commands helper bar."""
        is_hidden = "hidden" in self.slash_container.classes
        if is_hidden:
            self.slash_container.classes(remove="hidden")
        else:
            self.slash_container.classes(add="hidden")

    def _handle_input_change(self, e: Any) -> None:
        val = self.input.value or ""
        if val.startswith("/"):
            self.slash_container.classes(remove="hidden")
            # Show command ghost hint if appropriate
            if val.startswith("/plan"):
                self.hint_label.text = "[outline steps before tool execution]"
                self.hint_label.classes(remove="hidden")
            elif val.startswith("/goal"):
                self.hint_label.text = "[autonomous objective]"
                self.hint_label.classes(remove="hidden")
            else:
                self.hint_label.classes(add="hidden")
        else:
            self.slash_container.classes(add="hidden")
            self.hint_label.classes(add="hidden")

    def _select_slash_command(self, cmd: str) -> None:
        self.input.set_value(f"{cmd} ")
        self.slash_container.classes(add="hidden")

    def _handle_keydown(self, e: Any) -> None:
        args = getattr(e, "args", {}) or {}
        ctrl_key = args.get("ctrlKey", False)
        shift_key = args.get("shiftKey", False)
        if not shift_key or ctrl_key:
            self.submit()

    def _handle_action_click(self) -> None:
        if self.is_running:
            self.abort()
        else:
            self.submit()

    def set_text(self, text: str) -> None:
        """Set the input value."""
        self.input.set_value(text)

    def get_text(self) -> str:
        """Return the current input value stripped of trailing whitespace."""
        val = self.input.value or ""
        return val.strip()

    def submit(self) -> None:
        """Submit the current prompt to the turn loop."""
        text = self.get_text()
        if not text and not self.attachments:
            return
        self.input.set_value("")
        self.slash_container.classes(add="hidden")
        self.hint_label.classes(add="hidden")
        self.attachments.clear()
        self._render_attachments()
        if self.on_send:
            self.on_send(text)

    def abort(self) -> None:
        """Trigger cooperative cancellation."""
        if self.on_abort:
            self.on_abort()

    def set_running(self, running: bool) -> None:
        """Toggle action button between running (abort) and idle (send)."""
        self.is_running = running
        if running:
            self.action_btn.props("icon=stop color=negative").tooltip("Stop (Esc)")
            self.stop_btn.classes(remove="hidden")
        else:
            self.action_btn.props("icon=arrow_upward color=primary").tooltip(
                "Send (Enter)"
            )
            self.stop_btn.classes(add="hidden")

    def update_metrics(self, metrics: MthSessionStats) -> None:
        """Forward metric updates to stats pills."""
        self.stats_pills.update_metrics(metrics)

    def update_context_occupancy(self, occupancy: MthContextOccupancy) -> None:
        """Forward context usage updates to the context meter."""
        self.context_occupancy = occupancy
        self.context_meter.set_occupancy(occupancy)

    def matches_slash_command(self, prefix: str) -> list[str]:
        """Filter known slash commands matching input prefix."""
        if not prefix.startswith("/"):
            return []
        prefix_lower = prefix.lower()
        return [
            cmd for cmd in self.slash_commands if cmd.lower().startswith(prefix_lower)
        ]
