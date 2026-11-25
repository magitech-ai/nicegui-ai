"""Full application shell for Magitech Harness (MTH) in NiceGUI."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from .composer import MthComposer
from .inspector_drawer import MthInspectorDrawer
from .session_drawer import MthSessionDrawer
from .state import MthAppState, MthDiffItem
from .theme import setup_mth_theme
from .timeline import MthTimeline


class MthApp(ui.element):
    """Complete 1:1 Magitech Harness 3-Column Shell Frame in Python & NiceGUI."""

    def __init__(
        self,
        state: MthAppState | None = None,
        on_send_prompt: Callable[[str], Any] | None = None,
        on_abort_turn: Callable[[], Any] | None = None,
        on_run_terminal_command: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__("div")
        self.state = state or MthAppState()
        self.on_send_prompt = on_send_prompt
        self.on_abort_turn = on_abort_turn
        self.on_run_terminal_command = on_run_terminal_command

        self.classes("w-full h-screen overflow-hidden flex flex-col bg-[#090a0f]")
        setup_mth_theme()
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # 1. Top Bar
            with ui.row().classes(
                "w-full h-12 bg-[#11131a] border-b border-[#232736] px-3 flex items-center justify-between z-10 shrink-0"
            ):
                with ui.row().classes("items-center gap-2"):
                    # Sidebar Rail Toggle
                    self.sidebar_toggle_btn = (
                        ui.button(
                            icon="menu",
                            on_click=self.toggle_sidebar,
                        )
                        .props("dense flat round size=sm")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with self.sidebar_toggle_btn:
                        ui.tooltip("Toggle sidebar rail").classes("text-xs")

                    ui.icon("terminal", size="sm").classes("text-[#3b82f6]")
                    ui.label("Magitech Harness").classes(
                        "font-semibold text-sm tracking-wide text-white"
                    )
                    ui.badge(self.state.active_profile, color="blue-9").classes(
                        "font-mono text-[10px] uppercase"
                    )

                # Center: Active session title indicator
                active_sess = self.state.get_active_session()
                self.title_label = ui.label(
                    active_sess.title if active_sess else "Magitech Session"
                ).classes(
                    "text-xs font-medium text-slate-300 truncate max-w-sm hidden md:block"
                )

                # Right cluster: Profile Selector + Inspector Toggle
                with ui.row().classes("items-center gap-2"):
                    ui.label("Profile:").classes("text-xs text-slate-400 font-mono")
                    self.profile_select = (
                        ui.select(
                            options=self.state.profiles,
                            value=self.state.active_profile,
                            on_change=lambda e: self._handle_profile_change(e.value),
                        )
                        .props("dense borderless options-dense")
                        .classes("text-xs font-mono text-slate-200")
                    )

                    # Right Inspector Toggle Button
                    self.inspector_toggle_btn = (
                        ui.button(
                            icon="vertical_split",
                            on_click=self.toggle_inspector,
                        )
                        .props("dense flat round size=sm")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with self.inspector_toggle_btn:
                        ui.tooltip(
                            "Toggle right inspector (diff, files, terminal)"
                        ).classes("text-xs")

            # 2. 3-Column Shell Frame (Sidebar | Center Main | Right Inspector)
            with ui.row().classes("w-full flex-grow overflow-hidden"):
                # Left Column: Session Drawer (Rail or Drawer)
                self.session_drawer = MthSessionDrawer(
                    sessions=self.state.sessions,
                    active_session_id=self.state.active_session_id,
                    collapsed=self.state.sidebar_collapsed,
                    on_select_session=self._handle_session_select,
                    on_new_session=self._handle_new_session,
                    on_pin_session=self._handle_pin_session,
                    on_rename_session=self._handle_rename_session,
                    on_fork_session=self._handle_fork_session,
                    on_archive_session=self._handle_archive_session,
                    on_delete_session=self._handle_delete_session,
                    on_toggle_collapsed=self._handle_sidebar_toggle,
                )

                # Center Column: Timeline + Floating Composer Dock
                with ui.column().classes(
                    "flex-grow h-full relative overflow-hidden flex flex-col justify-between"
                ):
                    self.timeline = MthTimeline(
                        on_fork_turn=self._handle_fork_turn,
                        on_edit_prompt=self._handle_edit_prompt,
                    )

                    # Anchored Composer Dock with Stats Pills and Context Meter
                    with ui.column().classes("w-full max-w-3xl mx-auto p-4 z-10"):
                        self.composer = MthComposer(
                            on_send=self._handle_send,
                            on_abort=self._handle_abort,
                            on_model_change=self._handle_model_change,
                            on_permission_change=self._handle_permission_change,
                            on_plan_toggle=self._handle_plan_toggle,
                            metrics=self.state.metrics,
                            current_model=self.state.current_model,
                            available_models=self.state.available_models,
                            permission_preset=self.state.permission_preset,
                            context_occupancy=self.state.context_occupancy,
                        )

                # Right Column: Inspector Track (Document/Diff Preview, Files, Terminal)
                self.inspector_drawer = MthInspectorDrawer(
                    workspace_root=self.state.workspace_root,
                    active_diff=self.state.active_diff,
                    on_close=self.toggle_inspector,
                    on_file_select=self._handle_file_select,
                    on_run_command=self.on_run_terminal_command,
                )
                self.inspector_drawer.set_visibility(self.state.inspector_open)

    def toggle_sidebar(self) -> None:
        """Toggle left sidebar between collapsed rail and expanded drawer."""
        self.session_drawer.toggle()

    def _handle_sidebar_toggle(self, collapsed: bool) -> None:
        self.state.sidebar_collapsed = collapsed

    def toggle_inspector(self) -> None:
        """Toggle right inspector panel visibility."""
        is_open = self.state.toggle_inspector()
        self.inspector_drawer.set_visibility(is_open)

    def show_diff(self, diff_item: MthDiffItem) -> None:
        """Open inspector and display a unified diff."""
        self.state.set_active_diff(diff_item)
        self.inspector_drawer.show_diff(diff_item)
        self.inspector_drawer.set_visibility(True)

    def _handle_model_change(self, model: str, effort: str) -> None:
        self.state.set_model(model)
        self.state.set_reasoning_effort(effort)

    def _handle_permission_change(self, preset: str) -> None:
        self.state.set_permission_preset(preset)

    def _handle_plan_toggle(self, plan_mode: bool) -> None:
        self.state.plan_mode = plan_mode

    def _handle_profile_change(self, new_profile: str) -> None:
        self.state.active_profile = new_profile

    def _handle_session_select(self, session_id: str) -> None:
        self.state.active_session_id = session_id
        sess = self.state.get_active_session()
        if sess:
            self.title_label.set_text(sess.title)

    def _handle_new_session(self, workspace: str = "default") -> None:
        new_sess = self.state.create_session(workspace=workspace)
        self.session_drawer.sessions = self.state.sessions
        self.session_drawer.active_session_id = new_sess.id
        self.session_drawer.active_workspace = new_sess.workspace
        self.session_drawer._render_sessions()
        self.title_label.set_text(new_sess.title)

    def _handle_pin_session(self, session_id: str) -> None:
        self.state.pin_session(session_id)

    def _handle_rename_session(self, session_id: str, new_title: str) -> None:
        self.state.rename_session(session_id, new_title)
        if self.state.active_session_id == session_id:
            self.title_label.set_text(new_title)

    def _handle_fork_session(self, session_id: str) -> None:
        forked = self.state.fork_session(session_id)
        if forked:
            self.session_drawer.sessions = self.state.sessions
            self.session_drawer.active_session_id = forked.id
            self.session_drawer._render_sessions()
            self.title_label.set_text(forked.title)

    def _handle_archive_session(self, session_id: str) -> None:
        self.state.archive_session(session_id)

    def _handle_delete_session(self, session_id: str) -> None:
        self.state.delete_session(session_id)
        self.session_drawer.sessions = self.state.sessions
        self.session_drawer.active_session_id = self.state.active_session_id
        self.session_drawer._render_sessions()
        active = self.state.get_active_session()
        self.title_label.set_text(active.title if active else "Magitech Session")

    def _handle_file_select(self, file_path: str) -> None:
        self.inspector_drawer.show_file(file_path)

    def _handle_send(self, text: str) -> None:
        turn = self.state.add_turn(text)
        turn.is_deliberating = True
        self.timeline.render_turn(turn)
        self.timeline.start_running_tail("Thinking...")
        self.composer.set_running(True)
        if self.on_send_prompt:
            self.on_send_prompt(text)

    def _handle_abort(self) -> None:
        self.composer.set_running(False)
        self.timeline.stop_running_tail()
        active_turn = self.state.get_active_turn()
        if active_turn:
            self.timeline.set_reasoning_running(active_turn.turn_id, False)
        if self.on_abort_turn:
            self.on_abort_turn()

    def _handle_fork_turn(self, turn_id: str) -> None:
        """Fork active session at a specific historical turn."""
        sess = self.state.get_active_session()
        if sess:
            forked = self.state.create_session(
                title=f"Branch of {sess.title}", workspace=sess.workspace
            )
            for t in sess.turns:
                forked.turns.append(t)
                if t.turn_id == turn_id:
                    break
            self.session_drawer.sessions = self.state.sessions
            self.session_drawer.active_session_id = forked.id
            self.session_drawer._render_sessions()
            self.title_label.set_text(forked.title)

    def _handle_edit_prompt(self, text: str) -> None:
        """Set user text back into composer for editing and retrying."""
        self.composer.set_text(text)


def register_mth_routes(prefix: str = "") -> None:
    """Register the MTH page route on the active NiceGUI app."""
    route_path = prefix or "/"

    @ui.page(route_path)
    def _mth_route() -> None:
        setup_mth_theme()
        MthApp()


def main() -> None:
    """Launch the standalone Magitech Harness Desktop & Web UI server."""
    register_mth_routes("/")
    ui.run(
        title="Magitech Harness",
        port=8080,
        dark=True,
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
