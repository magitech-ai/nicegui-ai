import asyncio
import inspect
import os
from collections.abc import Callable
from typing import Any, Literal
from urllib.parse import parse_qs

from fastapi import Request
from nicegui import ui

from nicegui_ai.adapters import BaseStreamAdapter

from .automations_view import AutomationsView
from .auxiliary_pane import AuxiliaryPane, AuxTabType, ChangedFile
from .chat_view import ChatView
from .customizations_view import WorkspaceCustomizationsView
from .history_view import ConversationHistoryView, SearchConversationsModal
from .model_selector import AntigravityModelDef
from .settings_modal import SettingsModal
from .sidebar import CenterViewType, Sidebar
from .state import (
    AppSettings,
    ArtifactItem,
    AutomationItem,
    ContextAttachment,
    Message,
    PersonaConfig,
    ProjectConfig,
    Session,
    ThinkingBlock,
    ToolCallItem,
    create_default_artifact,
    create_default_automations,
    create_default_sessions,
    create_default_settings,
    create_default_skills,
    create_default_subagents,
)
from .terminal_dock import TerminalDock
from .theme import setup_antigravity_theme
from .title_bar import TitleBar


class AntigravityApp(ui.element):
    """Complete 1:1 Antigravity Desktop UI/UX Application Shell in Python & NiceGUI."""

    def __init__(
        self,
        *,
        query_params: dict[str, str] | None = None,
        stream_adapter: BaseStreamAdapter | None = None,
        persona: PersonaConfig | None = None,
        sessions: list[Session] | None = None,
        active_session_id: str | None = None,
        changed_files: list[ChangedFile] | None = None,
        on_send_message: Callable[[str, list[ContextAttachment]], Any] | None = None,
        on_approve_tool: Callable[[str], Any] | None = None,
        on_veto_tool: Callable[[str], Any] | None = None,
        on_minimize: Callable[[], None] | None = None,
        on_maximize: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
        show_window_controls: bool = False,
        on_select_session: Callable[[str], Any] | None = None,
        on_new_conversation: Callable[[], Any] | None = None,
        on_open_artifact: Callable[[ArtifactItem], Any] | None = None,
        is_streaming: bool = False,
        on_stop_generation: Callable[[], Any] | None = None,
        elapsed_time: str | None = None,
        attachments: list[ContextAttachment] | None = None,
        on_remove_attachment: Callable[[str], Any] | None = None,
        autocomplete_service: Any | None = None,
        models: list[AntigravityModelDef] | None = None,
        custom_center_view_renderer: Callable[[str], bool] | None = None,
        projects: list[ProjectConfig] | None = None,
        active_project_id: str | None = None,
        on_select_project: Callable[[str], Any] | None = None,
        on_delete_session: Callable[[str], Any] | None = None,
        on_open_settings: Callable[[str | None], Any] | None = None,
        on_settings_change: Callable[[AppSettings], Any] | None = None,
        on_model_change: Callable[[str], Any] | None = None,
        on_effort_change: Callable[[Literal["Low", "Medium", "High"]], Any]
        | None = None,
        mvge_data: dict[str, Any] | None = None,
        ecosystem_data: dict[str, Any] | None = None,
        checkpoints: list[dict[str, Any]] | None = None,
        selected_checkpoint_leaf: str | None = None,
        artifacts_list: list[dict[str, Any]] | None = None,
        live_submvges: list[dict[str, Any]] | None = None,
        workspace_files: list[dict[str, Any]] | None = None,
        terminal_dock_open: bool = False,
        terminal_lines: list[dict[str, Any]] | None = None,
        background_tasks: list[dict[str, Any]] | None = None,
        terminal_cwd: str = "",
        on_execute_terminal_command: Callable[[str], Any] | None = None,
        on_clear_terminal: Callable[[], Any] | None = None,
        on_kill_task: Callable[[str], Any] | None = None,
        on_toggle_terminal_dock: Callable[[bool], Any] | None = None,
        on_mvge_action: Callable[[str, dict[str, Any]], Any] | None = None,
        on_ecosystem_action: Callable[[str, dict[str, Any]], Any] | None = None,
        on_aux_action: Callable[[str, dict[str, Any]], Any] | None = None,
    ) -> None:
        super().__init__("div")
        params = query_params or {}
        self.params = params
        self.stream_adapter = stream_adapter
        self.persona = persona or PersonaConfig()
        self.changed_files = changed_files
        self.external_on_send_message = on_send_message
        self.on_approve_tool = on_approve_tool
        self.on_veto_tool = on_veto_tool
        self.on_minimize = on_minimize
        self.on_maximize = on_maximize
        self.on_close = on_close
        self.show_window_controls = show_window_controls
        self.on_select_session = on_select_session
        self.on_new_conversation = on_new_conversation
        self.on_open_artifact = on_open_artifact
        self.is_streaming = is_streaming
        self.on_stop_generation = on_stop_generation
        self.elapsed_time = elapsed_time
        self.attachments = list(attachments or [])
        self.on_remove_attachment = on_remove_attachment
        self.autocomplete_service = autocomplete_service
        self.models = models
        self.custom_center_view_renderer = custom_center_view_renderer
        self.on_select_project = on_select_project
        self.on_delete_session = on_delete_session
        self.on_open_settings = on_open_settings
        self.on_settings_change = on_settings_change
        self.on_model_change = on_model_change
        self.on_effort_change = on_effort_change
        self.mvge_data = mvge_data
        self.ecosystem_data = ecosystem_data
        self.checkpoints = checkpoints
        self.selected_checkpoint_leaf = selected_checkpoint_leaf
        self.artifacts_list = artifacts_list
        self.live_submvges = live_submvges
        self.workspace_files = workspace_files or []
        self.terminal_dock_open = (
            terminal_dock_open
            or params.get("openTerminalDock") == "true"
            or params.get("openTerminal") == "true"
        )
        self.terminal_lines = terminal_lines
        self.background_tasks = background_tasks
        self.terminal_cwd = terminal_cwd
        self.on_execute_terminal_command = on_execute_terminal_command
        self.on_clear_terminal = on_clear_terminal
        self.on_kill_task = on_kill_task
        self.on_toggle_terminal_dock = on_toggle_terminal_dock
        self.on_mvge_action = on_mvge_action
        self.on_ecosystem_action = on_ecosystem_action
        self.on_aux_action = on_aux_action
        self.mvge_mode = (
            self.persona.app_name == "Mvge"
            or mvge_data is not None
            or ecosystem_data is not None
            or on_mvge_action is not None
        )

        # Core State

        self.settings = create_default_settings()
        if projects is not None:
            self.settings.projects = list(projects)
        self.sessions = sessions if sessions is not None else create_default_sessions()
        self.automations = create_default_automations()
        self.subagents = [] if self.mvge_mode else create_default_subagents()
        self.skills = [] if self.mvge_mode else create_default_skills()
        if self.mvge_mode:
            if artifacts_list:
                art0 = artifacts_list[0]
                self.active_artifact = ArtifactItem(
                    id=art0.get("id", "art-1"),
                    title=art0.get("title", "Artifact"),
                    type=art0.get("type", "markdown"),
                    content=art0.get("content", ""),
                    description=art0.get("summary"),
                )
            else:
                self.active_artifact = None
        else:
            self.active_artifact = create_default_artifact()

        # Deep-link URL Query Parameter States (all 26 states supported)
        open_zero_state = params.get("openZeroState") == "true"
        if active_session_id is not None:
            self.active_session_id = active_session_id
        else:
            self.active_session_id = (
                "session-zero-state" if open_zero_state else "session-clone-rea"
            )
        raw_view = params.get("view", "chat")
        self.center_view: str = raw_view
        self.sidebar_open = True
        self.aux_open = params.get("openAux", "true") != "false"
        raw_aux_tab = params.get("auxTab", "terminal")
        self.aux_tab: AuxTabType = (
            raw_aux_tab  # type: ignore[assignment]
            if raw_aux_tab
            in (
                "overview",
                "review",
                "terminal",
                "file",
                "browser",
                "agents",
                "new-tab",
            )
            else "terminal"
        )

        self.settings_open = params.get("openSettings") == "true"
        self.settings_screen = params.get("settingsScreen", "general")
        self.search_modal_open = params.get("openSearch") == "true"
        self.selected_model = "Gemini 3.8 Flash High"
        self.selected_effort: Literal["Low", "Medium", "High"] = "High"
        self.active_project_id: str | None = (
            active_project_id
            if active_project_id is not None
            else (self.settings.projects[0].id if self.settings.projects else None)
        )

        # Navigation Back/Forward Stack
        self.nav_history: list[tuple[CenterViewType, str]] = [
            (self.center_view, self.active_session_id)
        ]
        self.nav_index = 0

        self.props('data-testid="antigravity-app-shell"')
        self.classes(
            "w-screen h-screen flex flex-col bg-[#101010] text-[#cccccc] overflow-hidden select-none"
        )
        self.render()

    def _active_session(self) -> Session:

        return next(
            (s for s in self.sessions if s.id == self.active_session_id),
            self.sessions[0],
        )

    def _push_nav(self, view: CenterViewType, session_id: str) -> None:
        self.nav_history = self.nav_history[: self.nav_index + 1]
        self.nav_history.append((view, session_id))
        self.nav_index = len(self.nav_history) - 1

    def render(self) -> None:
        self.clear()
        with self:
            # 1. 35px Native Top Menu Bar
            TitleBar(
                on_new_conversation=lambda: self._handle_new_conversation(None),
                on_toggle_sidebar=self._handle_toggle_sidebar,
                on_toggle_aux=self._handle_toggle_aux,
                on_open_settings=lambda: self._handle_open_settings("general"),
                on_open_history=self._handle_open_history,
                on_open_automations=self._handle_open_automations,
                on_open_customizations=self._handle_open_customizations,
                on_open_search=lambda: self._handle_set_search_modal(True),
                on_select_aux_tab=self._handle_select_aux_tab_str,
                initial_open_menu=self.params.get("openMenu"),
                persona=self.persona,
                on_minimize=self.on_minimize,
                on_maximize=self.on_maximize,
                on_close=self.on_close,
                show_window_controls=self.show_window_controls,
            )

            # 2. Main 3-Column Workspace Area (Sidebar + Center View + Auxiliary Pane)
            with ui.row().classes(
                "flex-1 w-full min-h-0 overflow-hidden gap-0 no-wrap relative"
            ):
                if self.sidebar_open:
                    Sidebar(
                        active_session_id=self.active_session_id,
                        active_center_view=self.center_view,
                        sessions=self.sessions,
                        projects=self.settings.projects,
                        on_select_session=self._handle_select_session,
                        on_new_conversation=self._handle_new_conversation,
                        on_open_history=self._handle_open_history,
                        on_open_automations=self._handle_open_automations,
                        on_open_customizations=self._handle_open_customizations,
                        on_open_settings=lambda: self._handle_open_settings("general"),
                        on_open_search_modal=lambda: self._handle_set_search_modal(
                            True
                        ),
                        on_toggle_sidebar=self._handle_toggle_sidebar,
                        on_toggle_pin=self._handle_toggle_pin,
                        on_toggle_archive=self._handle_toggle_archive,
                        on_delete_session=self._handle_delete_session,
                        on_add_project=self._handle_add_project,
                        on_navigate_back=self._handle_nav_back,
                        on_navigate_forward=self._handle_nav_forward,
                        can_navigate_back=self.nav_index > 0,
                        can_navigate_forward=self.nav_index < len(self.nav_history) - 1,
                        persona=self.persona,
                    )

                # Center Column (Center View + Bottom Terminal Dock)
                with ui.column().classes("flex-1 min-w-0 h-full flex flex-col"):
                    with ui.element("div").classes(
                        "flex-1 min-h-0 w-full overflow-hidden flex flex-col"
                    ):
                        if (
                            self.custom_center_view_renderer
                            and self.custom_center_view_renderer(self.center_view)
                        ):
                            pass
                        elif self.center_view == "history":
                            ConversationHistoryView(
                                sessions=self.sessions,
                                projects=self.settings.projects,
                                active_session_id=self.active_session_id,
                                on_select_session=self._handle_select_session,
                                on_toggle_pin=self._handle_toggle_pin,
                                on_toggle_archive=self._handle_toggle_archive,
                                on_delete_session=self._handle_delete_session,
                                on_new_conversation=lambda: (
                                    self._handle_new_conversation(None)
                                ),
                            )
                        elif self.center_view == "automations":
                            AutomationsView(
                                automations=self.automations,
                                projects=self.settings.projects,
                                on_toggle_automation=self._handle_toggle_automation,
                                on_delete_automation=self._handle_delete_automation,
                                on_create_automation=self._handle_create_automation,
                                on_update_automation=self._handle_update_automation,
                                on_run_automation_now=self._handle_run_automation_now,
                                initial_modal_open=self.params.get("openNewAutomation")
                                == "true",
                                initial_selected_trigger_id=self.params.get(
                                    "triggerId"
                                ),
                            )
                        elif self.center_view == "customizations":
                            WorkspaceCustomizationsView(
                                projects=self.settings.projects,
                                active_project_id=self.active_project_id,
                                initial_tab=self.params.get(
                                    "customizationsTab", "runes"
                                ),
                                on_select_project=self._handle_select_project,
                                on_open_global_customizations=lambda: (
                                    self._handle_open_settings("customizations")
                                ),
                                on_open_file_in_aux=self._handle_open_file_in_aux,
                                persona=self.persona,
                                ecosystem_data=self.ecosystem_data,
                                on_ecosystem_action=self.on_ecosystem_action,
                            )
                        else:
                            ChatView(
                                session=self._active_session(),
                                all_sessions=self.sessions,
                                projects=self.settings.projects,
                                settings=self.settings,
                                selected_model=self.selected_model,
                                selected_effort=self.selected_effort,
                                is_streaming=self.is_streaming,
                                is_aux_open=self.aux_open,
                                initial_open_model=self.params.get("openModel")
                                == "true",
                                initial_open_context=self.params.get("openContext")
                                == "true",
                                initial_open_kebab=self.params.get("openKebab")
                                == "true",
                                initial_open_modes=self.params.get("openModes")
                                == "true",
                                initial_open_side_question=self.params.get(
                                    "openSideQuestion"
                                )
                                == "true",
                                initial_open_fastpick=self.params.get("openFastpick")
                                == "true",
                                initial_open_lifted_menu=self.params.get(
                                    "openLiftedMenu"
                                )
                                == "true",
                                on_send_message=self._handle_send_message,
                                on_select_session=self._handle_select_session,
                                on_open_artifact=self._handle_open_artifact,
                                on_toggle_aux=self._handle_toggle_aux,
                                on_open_aux_tab=self._handle_open_aux_tab,
                                on_open_settings=self._handle_open_settings,
                                on_model_change=self._handle_model_change,
                                on_effort_change=self._handle_effort_change,
                                on_fork_from_message=self._handle_fork_from_message,
                                persona=self.persona,
                                on_approve_tool=self.on_approve_tool,
                                on_veto_tool=self.on_veto_tool,
                                on_stop_generation=self.on_stop_generation,
                                elapsed_time=self.elapsed_time,
                                attachments=self.attachments,
                                on_remove_attachment=self.on_remove_attachment,
                                autocomplete_service=self.autocomplete_service,
                                models=self.models,
                            )

                    # Bottom Terminal Dock
                    TerminalDock(
                        is_open=self.terminal_dock_open,
                        cwd=self.terminal_cwd,
                        terminal_lines=self.terminal_lines,
                        background_tasks=self.background_tasks,
                        on_execute_command=self._handle_execute_terminal_command,
                        on_clear=self._handle_clear_terminal,
                        on_kill_task=self._handle_kill_task,
                        on_toggle=self._handle_toggle_terminal_dock,
                    )

                # Right Auxiliary Pane
                AuxiliaryPane(
                    is_open=self.aux_open,
                    active_artifact=self.active_artifact,
                    subagents=self.subagents,
                    artifact_width=self.settings.artifact_width,
                    initial_tab=self.aux_tab,
                    initial_open_plus=self.params.get("openAuxPlus") == "true",
                    initial_open_overview_customize=self.params.get(
                        "openOverviewCustomize"
                    )
                    == "true",
                    initial_open_diff_comment=self.params.get("openDiffComment")
                    == "true",
                    on_close=self._handle_toggle_aux,
                    on_tab_change=self._handle_aux_tab_change,
                    changed_files=self.changed_files,
                    persona=self.persona,
                    mvge_mode=self.mvge_mode,
                    checkpoints=self.checkpoints,
                    selected_checkpoint_leaf=self.selected_checkpoint_leaf,
                    artifacts_list=self.artifacts_list,
                    live_submvges=self.live_submvges,
                    workspace_files=self.workspace_files,
                    on_aux_action=self._handle_aux_action,
                )

            # 3. Modals (Search Command Palette + 2-Column Settings Modal)
            SearchConversationsModal(
                is_open=self.search_modal_open,
                on_close=lambda: self._handle_set_search_modal(False),
                sessions=self.sessions,
                projects=self.settings.projects,
                on_select_session=self._handle_select_session_from_modal,
                on_new_conversation=lambda: self._handle_new_conversation(None),
                on_open_automations=self._handle_open_automations,
                on_open_settings=lambda: self._handle_open_settings("general"),
            )

            SettingsModal(
                is_open=self.settings_open,
                initial_screen=self.settings_screen,
                settings=self.settings,
                skills=self.skills,
                persona=self.persona,
                mvge_data=self.mvge_data,
                on_mvge_action=self.on_mvge_action,
                on_close=self._handle_close_settings,
                on_settings_change=self._handle_settings_change,
            )

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    def _handle_select_session(self, session_id: str) -> None:
        self.active_session_id = session_id
        self.center_view = "chat"
        self._push_nav("chat", session_id)
        if self.on_select_session:
            res = self.on_select_session(session_id)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.create_task(res)
        self.render()

    def _handle_select_session_from_modal(self, session_id: str) -> None:
        self.search_modal_open = False
        self._handle_select_session(session_id)

    def _handle_new_conversation(self, project_id: str | None) -> None:
        zero_sess = next(
            (s for s in self.sessions if s.id == "session-zero-state"), None
        )
        if zero_sess and project_id:
            zero_sess.project_id = project_id
        self.active_session_id = "session-zero-state"
        self.center_view = "chat"
        self.search_modal_open = False
        self._push_nav("chat", "session-zero-state")
        if self.on_new_conversation:
            res = self.on_new_conversation()
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.create_task(res)
        self.render()

    def _handle_open_history(self) -> None:
        self.center_view = "history"
        self._push_nav("history", self.active_session_id)
        self.render()

    def _handle_open_automations(self) -> None:
        self.center_view = "automations"
        self.search_modal_open = False
        self._push_nav("automations", self.active_session_id)
        self.render()

    def _handle_open_customizations(self) -> None:
        self.center_view = "customizations"
        self._push_nav("customizations", self.active_session_id)
        self.render()

    def _handle_open_settings(self, screen: str | None = None) -> None:
        if self.on_open_settings is not None:
            res = self.on_open_settings(screen)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)
            return
        self.settings_open = True
        self.search_modal_open = False
        if screen:
            self.settings_screen = screen
        self.render()

    def _handle_close_settings(self) -> None:
        self.settings_open = False
        self.render()

    def _handle_settings_change(self, updated_settings: AppSettings) -> None:
        self.settings = updated_settings
        if self.on_settings_change is not None:
            res = self.on_settings_change(updated_settings)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)
        self.render()

    def _handle_set_search_modal(self, open_state: bool) -> None:
        self.search_modal_open = open_state
        self.render()

    def _handle_toggle_sidebar(self) -> None:
        self.sidebar_open = not self.sidebar_open
        self.render()

    def _handle_toggle_aux(self) -> None:
        self.aux_open = not self.aux_open
        self.render()

    def _handle_open_aux_tab(self, tab: AuxTabType) -> None:
        self.aux_open = True
        self.aux_tab = tab
        self.render()

    def _handle_select_aux_tab_str(self, tab: str) -> None:
        if tab in (
            "overview",
            "review",
            "terminal",
            "file",
            "browser",
            "agents",
            "new-tab",
        ):
            self._handle_open_aux_tab(tab)  # type: ignore[arg-type]

    def _handle_aux_tab_change(self, tab: AuxTabType) -> None:
        self.aux_tab = tab

    def _handle_open_artifact(self, artifact: ArtifactItem) -> None:
        self.active_artifact = artifact
        self.aux_open = True
        self.aux_tab = "file"
        if self.on_open_artifact:
            res = self.on_open_artifact(artifact)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)
        self.render()

    def _handle_open_file_in_aux(
        self, title: str, content: str, file_type: str
    ) -> None:
        self.active_artifact = ArtifactItem(
            id=f"art-{len(self.sessions)}",
            title=title,
            type="markdown",
            content=content,
            description=file_type,
        )
        self.aux_open = True
        self.aux_tab = "file"
        self.render()

    def _handle_toggle_pin(self, session_id: str) -> None:
        for s in self.sessions:
            if s.id == session_id:
                s.pinned = not s.pinned
        self.render()

    def _handle_toggle_archive(self, session_id: str) -> None:
        for s in self.sessions:
            if s.id == session_id:
                s.archived = not s.archived
        self.render()

    def _handle_delete_session(self, session_id: str) -> None:
        self.sessions = [
            s
            for s in self.sessions
            if s.id != session_id or s.id == "session-zero-state"
        ]
        if self.active_session_id == session_id:
            self.active_session_id = "session-zero-state"
        if self.on_delete_session is not None:
            res = self.on_delete_session(session_id)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)
        self.render()

    def _handle_add_project(self, path: str) -> None:
        name = path.rstrip("/").split("/")[-1] or "new-project"
        new_proj = ProjectConfig(
            id=f"proj-{len(self.settings.projects) + 1}",
            name=name,
            folders=[path],
            active_conversations=0,
            archived_conversations=0,
        )
        self.settings.projects.append(new_proj)
        self.render()

    def _handle_select_project(self, project_id: str) -> None:
        self.active_project_id = project_id
        if self.on_select_project is not None:
            res = self.on_select_project(project_id)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)
        self.render()

    def _handle_nav_back(self) -> None:
        if self.nav_index > 0:
            self.nav_index -= 1
            view, sid = self.nav_history[self.nav_index]
            self.center_view = view
            self.active_session_id = sid
            self.render()

    def _handle_nav_forward(self) -> None:
        if self.nav_index < len(self.nav_history) - 1:
            self.nav_index += 1
            view, sid = self.nav_history[self.nav_index]
            self.center_view = view
            self.active_session_id = sid
            self.render()

    def _handle_toggle_automation(self, auto_id: str) -> None:
        for a in self.automations:
            if a.id == auto_id:
                a.enabled = not a.enabled
        self.render()

    def _handle_delete_automation(self, auto_id: str) -> None:
        self.automations = [a for a in self.automations if a.id != auto_id]
        self.render()

    def _handle_create_automation(self, item: AutomationItem) -> None:
        self.automations.insert(0, item)
        self.render()

    def _handle_update_automation(self, updated: AutomationItem) -> None:
        self.automations = [
            updated if a.id == updated.id else a for a in self.automations
        ]
        self.render()

    def _handle_run_automation_now(self, item: AutomationItem) -> None:
        self._handle_send_message(
            f"[Automation: {item.display_name}] {item.prompt}", []
        )

    def _handle_model_change(self, model: str) -> None:
        self.selected_model = model
        if self.on_model_change:
            res = self.on_model_change(model)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_effort_change(self, effort: Literal["Low", "Medium", "High"]) -> None:
        self.selected_effort = effort
        if self.on_effort_change:
            res = self.on_effort_change(effort)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_toggle_terminal_dock(self, open_state: bool) -> None:
        self.terminal_dock_open = open_state
        self.render()
        if self.on_toggle_terminal_dock:
            res = self.on_toggle_terminal_dock(open_state)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_execute_terminal_command(self, cmd: str) -> None:
        if self.on_execute_terminal_command:
            res = self.on_execute_terminal_command(cmd)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_clear_terminal(self) -> None:
        if self.on_clear_terminal:
            res = self.on_clear_terminal()
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_kill_task(self, task_id: str) -> None:
        if self.on_kill_task:
            res = self.on_kill_task(task_id)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_aux_action(self, action: str, payload: dict[str, Any]) -> None:
        if action == "toggle_terminal_dock":
            self._handle_toggle_terminal_dock(not self.terminal_dock_open)
            return
        if self.on_aux_action:
            res = self.on_aux_action(action, payload)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.create_task(res)

    def _handle_fork_from_message(self, msg_id: str) -> None:
        curr = self._active_session()
        cutoff_msgs: list[Message] = []
        for m in curr.messages:
            cutoff_msgs.append(m)
            if m.id == msg_id:
                break
        forked = Session(
            id=f"session-fork-{len(self.sessions) + 1}",
            title=f"{curr.title} (Fork)",
            timestamp="Just now",
            token_count=curr.token_count // 2,
            project_id=curr.project_id,
            pinned=True,
            messages=cutoff_msgs,
        )
        self.sessions.insert(1, forked)
        self.active_session_id = forked.id
        self.render()

    def _handle_send_message(
        self, text: str, attachments: list[ContextAttachment]
    ) -> None:
        if self.external_on_send_message:
            res = self.external_on_send_message(text, attachments)
            if inspect.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.create_task(res)
            return

        sess = self._active_session()
        if sess.id == "session-zero-state":
            new_sess = Session(
                id=f"session-{len(self.sessions) + 1}",
                title=text[:44],
                timestamp="Just now",
                token_count=1250,
                project_id=self.active_project_id,
                pinned=True,
                messages=[],
            )
            self.sessions.insert(1, new_sess)
            self.active_session_id = new_sess.id
            sess = new_sess

        user_msg = Message(
            id=f"msg-u-{len(sess.messages) + 1}",
            role="user",
            content=text,
            timestamp="Just now",
            attachments=attachments,
        )
        sess.messages.append(user_msg)

        agent_msg = Message(
            id=f"msg-a-{len(sess.messages) + 1}",
            role="agent",
            content=(
                f"Executed request with **{self.selected_model}** (`{self.selected_effort}` effort).\n\n"
                f"Verified workspace state in `/mnt/storage/projects/nicegui-ai`."
            ),
            timestamp="Just now",
            thinking=ThinkingBlock(
                duration="2s",
                steps=[
                    f"Routing prompt through {self.selected_model} ({self.selected_effort} reasoning effort)",
                    "Inspecting nicegui_ai.antigravity workspace state",
                ],
            ),
            tool_calls=[
                ToolCallItem(
                    id=f"tc-auto-{len(sess.messages)}",
                    tool_name="run_command",
                    action="Verifying nicegui_ai test suite",
                    parameters={"command": "uv run pytest -q"},
                    output="28 passed in 0.84s",
                    status="completed",
                )
            ],
        )
        sess.messages.append(agent_msg)
        sess.token_count += 1800
        self.center_view = "chat"
        self.render()


def parse_request_query(request: Request | None) -> dict[str, str]:
    """Extract single-value query dict from a FastAPI Request."""
    if request is None:
        return {}
    raw = parse_qs(str(request.url.query))
    return {k: v[0] for k, v in raw.items() if v}


def register_antigravity_routes(prefix: str = "") -> None:
    """Register the 1:1 Antigravity page route on the active NiceGUI app."""
    route_path = prefix or "/"

    @ui.page(route_path)
    def _antigravity_route(request: Request) -> None:
        setup_antigravity_theme()
        params = parse_request_query(request)
        AntigravityApp(query_params=params)


def main() -> None:
    """Launch the standalone 1:1 Antigravity Desktop Clone server."""
    register_antigravity_routes("/")
    port = int(os.environ.get("PORT", "8080"))
    ui.run(
        title="Antigravity",
        port=port,
        dark=True,
        reload=False,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
