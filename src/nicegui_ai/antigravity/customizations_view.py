"""1:1 Antigravity Dedicated Workspace Customizations View (xUb / wUb).

Integrates the 7 unified Mvge & Mvge-Marketplace ecosystem surfaces:
1. runes: Marketplace profiles (minimal, coding, autonomous), 21 Runes, Seeker gateway
2. skills: Skills catalog, scope filtering, deduplication, WikiSkill autonomous evolution
3. steering: AGENTS.md layers (Global, Project, Subpackages) with editor and validator
4. mcp: Global and Workspace MCP servers, connection testing, status
5. okf: Open Knowledge Format v0.2 graph, concept trust levels, auto context budget
6. adrs: MADR 3.0 records, status, validation, scaffolding, index sync
7. selfmod: Extension paths, hot-reload candidate detection, snapshot rollback timeline
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from nicegui import ui

from nicegui_ai.antigravity.icons import AntigravityIcon
from nicegui_ai.antigravity.state import PersonaConfig, ProjectConfig


@dataclass
class SkillRuleEntry:
    id: str
    name: str
    description: str
    path: str
    scope: Literal["Workspace", "Global"]
    enabled: bool
    content: str
    trigger: str | None = None


@dataclass
class PluginEntry:
    id: str
    name: str
    version: str
    description: str
    path: str
    enabled: bool
    skills_count: int
    mcp_count: int


@dataclass
class CustomAgentEntry:
    id: str
    name: str
    role: str
    model: str
    path: str
    scope: Literal["Workspace", "Global"]
    enabled: bool


class WorkspaceCustomizationsView(ui.element):
    """Dedicated center view for managing Skills, Rules, Runes, and Mvge Ecosystem."""

    TAB_MAP: dict[str, str] = {
        "rules": "steering",
        "plugins": "runes",
        "agents": "runes",
    }

    def __init__(
        self,
        projects: list[ProjectConfig] | None = None,
        active_project_id: str | None = None,
        on_select_project: Callable[[str], None] | None = None,
        on_open_global_customizations: Callable[[], None] | None = None,
        on_open_file_in_aux: Callable[[str, str, str], None] | None = None,
        persona: PersonaConfig | None = None,
        initial_tab: str = "runes",
        ecosystem_data: dict[str, Any] | None = None,
        on_ecosystem_action: Callable[[str, dict[str, Any]], Any] | None = None,
    ) -> None:
        super().__init__("div")
        self.projects = projects or []
        self.active_project_id = active_project_id
        self.on_select_project = on_select_project
        self.on_open_global_customizations = on_open_global_customizations
        self.on_open_file_in_aux = on_open_file_in_aux
        self.persona = persona or PersonaConfig()
        self.ecosystem_data: dict[str, Any] = ecosystem_data or {}
        self.on_ecosystem_action = on_ecosystem_action

        self.mvge_mode = (
            self.persona.app_name == "Mvge"
            or ecosystem_data is not None
            or on_ecosystem_action is not None
        )

        norm_tab = self.TAB_MAP.get(initial_tab, initial_tab)
        self.active_tab: str = norm_tab
        self.search_query: str = ""
        self.scope_filter: Literal["all", "Workspace", "Global"] = "all"
        self.collapsed_sections: dict[str, bool] = {}

        # Default fallback entries for legacy tests and standalone mode
        self.skills: list[SkillRuleEntry] = [
            SkillRuleEntry(
                id="skill-nicegui",
                name="nicegui",
                description="Guidance for Python-first NiceGUI applications.",
                path="~/.agents/skills/nicegui/SKILL.md",
                scope="Global",
                enabled=True,
                content="---\nname: nicegui\n---\n# NiceGUI Skill\n",
            ),
            SkillRuleEntry(
                id="skill-tdd",
                name="tdd",
                description="Test-driven development red-green-refactor workflow.",
                path="~/.agents/skills/tdd/SKILL.md",
                scope="Global",
                enabled=True,
                content="---\nname: tdd\n---\n# Test-Driven Development\n",
            ),
            SkillRuleEntry(
                id="skill-git-workflow",
                name="git-workflow",
                description="Conventional commits and staging workflow.",
                path="~/.agents/skills/git-workflow/SKILL.md",
                scope="Workspace",
                enabled=True,
                content="---\nname: git-workflow\n---\n# Git Workflow\n",
            ),
        ]
        self.rules: list[SkillRuleEntry] = [
            SkillRuleEntry(
                id="rule-agents-md",
                name="AGENTS.md",
                description="Workspace steering and protocol instructions.",
                path="AGENTS.md",
                scope="Workspace",
                trigger="Always On",
                enabled=True,
                content="# AGENTS.md\n\nAdhere to the .agents standard.\n",
            ),
        ]
        self.plugins: list[PluginEntry] = []
        self.agents: list[CustomAgentEntry] = []

        self.props('data-testid="project-customizations-content"')
        self.classes(
            "flex-1 overflow-y-auto h-full min-h-0 bg-background text-foreground"
        )
        self.render_view()

    def set_tab(self, tab_id: str) -> None:
        """Switch the active ecosystem tab."""
        self.active_tab = self.TAB_MAP.get(tab_id, tab_id)
        self.render_view()

    def _dispatch_action(
        self, action: str, payload: dict[str, Any] | None = None
    ) -> Any:
        if self.on_ecosystem_action:
            return self.on_ecosystem_action(action, payload or {})
        return None

    # Public action handlers (called by tests and UI elements)
    def _handle_apply_profile(self, profile: str) -> None:
        self._dispatch_action("apply_profile", {"profile": profile})

    def _handle_activate_skill(self, name: str) -> None:
        self._dispatch_action("activate_skill", {"name": name})

    def _handle_save_steering(self, scope: str, content: str) -> None:
        self._dispatch_action("save_steering", {"scope": scope, "content": content})

    def _handle_test_mcp(self, name: str) -> None:
        self._dispatch_action("test_mcp_server", {"name": name})

    def _handle_verify_concept(self, concept_id: str) -> None:
        self._dispatch_action("okf_verify", {"concept_id": concept_id})

    def _handle_validate_adrs(self) -> None:
        self._dispatch_action("adr_validate", {})

    def _handle_rollback_snapshot(self, snapshot_id: str) -> None:
        self._dispatch_action("self_rollback", {"snapshot_id": snapshot_id})

    def _handle_toggle_rune(self, name: str, enabled: bool) -> None:
        self._dispatch_action("toggle_rune", {"name": name, "enabled": enabled})

    def _handle_configure_rune(self, name: str) -> None:
        self._dispatch_action("configure_rune", {"name": name})

    def _handle_install_rune(self, name: str) -> None:
        self._dispatch_action("install_rune", {"name": name})

    def _handle_uninstall_rune(self, name: str) -> None:
        self._dispatch_action("uninstall_rune", {"name": name})

    def _handle_dedupe_skills(self) -> None:
        self._dispatch_action("dedupe_skills", {})

    def _handle_scaffold_skill(self, name: str, desc: str) -> None:
        self._dispatch_action("scaffold_skill", {"name": name, "description": desc})

    def _handle_skill_evolution_consolidate(self) -> None:
        self._dispatch_action("skill_evolution_consolidate", {})

    def _handle_skill_evolution_propose(self) -> None:
        self._dispatch_action("skill_evolution_propose", {})

    def _handle_validate_steering(self) -> None:
        self._dispatch_action("validate_steering", {})

    def _handle_toggle_mcp(self, name: str, disabled: bool) -> None:
        self._dispatch_action(
            "toggle_mcp_server", {"name": name, "disabled": disabled}
        )

    def _handle_add_mcp(self, name: str, transport: str, command: str) -> None:
        self._dispatch_action(
            "add_mcp_server",
            {"name": name, "transport": transport, "command": command},
        )

    def _handle_okf_set_context(self, concept_id: str, context: str) -> None:
        self._dispatch_action(
            "okf_set_context", {"concept_id": concept_id, "context": context}
        )

    def _handle_okf_deprecate(self, concept_id: str) -> None:
        self._dispatch_action("okf_deprecate", {"concept_id": concept_id})

    def _handle_okf_validate(self) -> None:
        self._dispatch_action("okf_validate", {})

    def _handle_adr_new(self, title: str) -> None:
        self._dispatch_action("adr_new", {"title": title})

    def _handle_adr_sync(self) -> None:
        self._dispatch_action("adr_sync", {})

    def _handle_reload_mvge(self) -> None:
        self._dispatch_action("reload_mvge", {})

    def _handle_self_snapshot(self, label: str) -> None:
        self._dispatch_action("self_snapshot", {"label": label})

    def render_view(self) -> None:
        """Render the complete customizations view."""
        self.clear()
        active_project = next(
            (p for p in self.projects if p.id == self.active_project_id),
            self.projects[0] if self.projects else None,
        )

        with self:
            with ui.element("div").classes(
                "p-6 md:p-8 space-y-6 max-w-4xl mx-auto pb-24 flex flex-col"
            ):
                # Top Header Bar
                with ui.element("div").classes(
                    "flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4"
                ):
                    with ui.element("div").classes("flex flex-col gap-1 min-w-0"):
                        with ui.element("div").classes("flex items-center gap-2"):
                            ui.label("Ecosystem Customizations").classes(
                                "text-lg font-semibold text-foreground select-none tracking-tight"
                            )
                            ui.label(
                                active_project.name if active_project else "Workspace"
                            ).classes(
                                "text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-card-border font-medium"
                            )
                        ui.label(
                            "Unified surface for Runes, Skills Evolution, Steering, MCP Servers, OKF Graph, ADRs, and Self-Mod."
                        ).classes("text-xs text-muted-foreground")

                    with ui.element("div").classes("flex items-center gap-2 shrink-0"):
                        with (
                            ui.element("button")
                            .props('type="button"')
                            .classes(
                                "inline-flex items-center gap-1.5 h-8 px-3 rounded-lg bg-card "
                                "hover:bg-secondary text-secondary-foreground hover:text-foreground "
                                "text-xs font-medium border border-card-border cursor-pointer transition-colors"
                            )
                            .on("click", self.on_open_global_customizations)
                        ):
                            AntigravityIcon("settings", size=14)
                            ui.label("Global Config")

                # 7 Unified Ecosystem Tabs Bar
                tabs_spec = [
                    ("runes", "Profiles & Runes", "customizations"),
                    ("skills", "Skills & Evolution", "sparkles"),
                    ("steering", "Steering (AGENTS.md)", "file_doc"),
                    ("mcp", "MCP Servers", "tune"),
                    ("okf", "Knowledge Graph (OKF)", "folder"),
                    ("adrs", "Architecture (ADRs)", "review_tab"),
                    ("selfmod", "Self-Mod & Snapshots", "revert"),
                ]

                with (
                    ui.element("div")
                    .props('data-testid="ecosystem-tabs-bar"')
                    .classes(
                        "flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-card-border/60"
                    )
                ):
                    for tab_id, label, icon_name in tabs_spec:
                        is_active = self.active_tab == tab_id
                        with (
                            ui.element("button")
                            .props(f'type="button" data-testid="tab-{tab_id}"')
                            .classes(
                                "inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors whitespace-nowrap "
                                + (
                                    "bg-primary/15 text-primary border border-primary/30"
                                    if is_active
                                    else "text-muted-foreground hover:text-foreground hover:bg-secondary/60 border border-transparent"
                                )
                            )
                            .on("click", lambda _, t=tab_id: self.set_tab(t))
                        ):
                            AntigravityIcon(
                                icon_name,
                                size=13,
                                classes="text-primary"
                                if is_active
                                else "text-muted-foreground",
                            )
                            ui.label(label)

                # Tab Content Viewport
                with (
                    ui.element("div")
                    .props('data-testid="ecosystem-tab-content"')
                    .classes("flex flex-col gap-6 pt-2")
                ):
                    if self.active_tab == "runes":
                        self._render_runes_tab()
                    elif self.active_tab == "skills":
                        self._render_skills_tab()
                    elif self.active_tab == "steering":
                        self._render_steering_tab()
                    elif self.active_tab == "mcp":
                        self._render_mcp_tab()
                    elif self.active_tab == "okf":
                        self._render_okf_tab()
                    elif self.active_tab == "adrs":
                        self._render_adrs_tab()
                    elif self.active_tab == "selfmod":
                        self._render_selfmod_tab()
                    else:
                        self._render_runes_tab()

    # -------------------------------------------------------------------------
    # TAB 1: RUNES & PROFILES
    # -------------------------------------------------------------------------
    def _render_runes_tab(self) -> None:
        profiles_info = self.ecosystem_data.get("profiles", {})
        active_prof = profiles_info.get("active", "coding")
        available_profs = profiles_info.get(
            "available",
            [
                {
                    "name": "minimal",
                    "count": 4,
                    "desc": "Lean footprint: steering, approval, sessions",
                },
                {
                    "name": "coding",
                    "count": 12,
                    "desc": "Flagship developer: LSP, checkpoint, diffs, titles",
                },
                {
                    "name": "autonomous",
                    "count": 19,
                    "desc": "Full stack: submvges, evolution, ADRs, OKF, OTel",
                },
            ],
        )

        with ui.element("div").classes("flex flex-col gap-6"):
            # 1. Profiles Selection Strip
            with ui.element("div").classes("flex flex-col gap-2.5"):
                ui.label("Marketplace Profiles").classes(
                    "text-xs font-semibold text-foreground uppercase tracking-wider"
                )
                with ui.element("div").classes(
                    "grid grid-cols-1 md:grid-cols-3 gap-3"
                ):
                    for prof in available_profs:
                        pname = prof["name"]
                        is_curr = pname == active_prof
                        with ui.element("div").classes(
                            "flex flex-col justify-between p-3.5 rounded-xl border transition-all "
                            + (
                                "bg-primary/5 border-primary/40 shadow-sm"
                                if is_curr
                                else "bg-card border-card-border hover:border-card-border/80"
                            )
                        ):
                            with ui.element("div").classes("flex flex-col gap-1"):
                                with ui.element("div").classes(
                                    "flex items-center justify-between"
                                ):
                                    ui.label(pname.capitalize()).classes(
                                        "text-sm font-semibold text-foreground"
                                    )
                                    if is_curr:
                                        ui.label("Active").classes(
                                            "text-[10px] px-1.5 py-0.5 rounded-full bg-primary/20 text-primary font-medium"
                                        )
                                ui.label(
                                    prof.get("desc", f"{prof.get('count', 0)} Runes")
                                ).classes("text-xs text-muted-foreground line-clamp-2")

                            with ui.element("div").classes(
                                "flex items-center justify-between mt-3 pt-2 border-t border-card-border/40"
                            ):
                                ui.label(f"{prof.get('count', 0)} Runes").classes(
                                    "text-[11px] font-mono text-muted-foreground"
                                )
                                if not is_curr:
                                    with (
                                        ui.element("button")
                                        .props('type="button"')
                                        .classes(
                                            "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground cursor-pointer transition-colors"
                                        )
                                        .on(
                                            "click",
                                            lambda _, p=pname: self._handle_apply_profile(
                                                p
                                            ),
                                        )
                                    ):
                                        ui.label("Apply")

            # 2. Seeker Gateway Status Card
            with ui.element("div").classes(
                "p-4 rounded-xl border border-card-border bg-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            ):
                with ui.element("div").classes("flex items-center gap-3"):
                    AntigravityIcon("tune", size=18, classes="text-primary")
                    with ui.element("div").classes("flex flex-col gap-0.5"):
                        with ui.element("div").classes("flex items-center gap-2"):
                            ui.label("Seeker Tool Gateway").classes(
                                "text-sm font-medium text-foreground"
                            )
                            ui.label("Active").classes(
                                "text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            )
                        ui.label(
                            "Preserves Mana Pool: Tools hidden from initial context; auto-evicted after 8 turns idle TTL."
                        ).classes("text-xs text-muted-foreground")

            # 3. 21 Runes Catalog
            runes_list = self.ecosystem_data.get("runes", [])
            with ui.element("div").classes("flex flex-col gap-3"):
                with ui.element("div").classes(
                    "flex items-center justify-between px-1"
                ):
                    ui.label(f"Installed Runes ({len(runes_list)})").classes(
                        "text-xs font-semibold text-foreground uppercase tracking-wider"
                    )
                    ui.label("~/.agents/extensions/*").classes(
                        "text-[11px] font-mono text-muted-foreground"
                    )

                with ui.element("div").classes(
                    "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
                ):
                    if not runes_list:
                        with ui.element("div").classes(
                            "p-6 text-center text-xs text-muted-foreground"
                        ):
                            ui.label("No Runes loaded in this session.")
                    else:
                        for rune in runes_list:
                            rname = rune.get("name", "")
                            renabled = rune.get("enabled", True)
                            with ui.element("div").classes(
                                "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                            ):
                                with ui.element("div").classes(
                                    "flex flex-col gap-1 min-w-0 flex-1"
                                ):
                                    with ui.element("div").classes(
                                        "flex flex-wrap items-center gap-2"
                                    ):
                                        AntigravityIcon(
                                            "customizations",
                                            size=14,
                                            classes="text-primary",
                                        )
                                        ui.label(rname).classes(
                                            "text-sm font-medium text-foreground"
                                        )
                                        if rune.get("version"):
                                            ui.label(f"v{rune['version']}").classes(
                                                "text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-muted-foreground border border-card-border"
                                            )
                                        for t in rune.get("types", []):
                                            ui.label(t).classes(
                                                "text-[10px] px-1.5 py-0.2 rounded bg-secondary/80 text-secondary-foreground border border-card-border"
                                            )
                                    ui.label(
                                        rune.get(
                                            "description", "Mvge runtime extension."
                                        )
                                    ).classes("text-xs text-muted-foreground line-clamp-1")

                                with ui.element("div").classes(
                                    "flex items-center gap-2 shrink-0"
                                ):
                                    if rune.get("has_settings"):
                                        with (
                                            ui.element("button")
                                            .props('type="button"')
                                            .classes(
                                                "p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground cursor-pointer"
                                            )
                                            .on(
                                                "click",
                                                lambda _, n=rname: self._handle_configure_rune(
                                                    n
                                                ),
                                            )
                                        ):
                                            AntigravityIcon("settings", size=13)

                                    with (
                                        ui.element("button")
                                        .props('type="button" role="switch"')
                                        .classes(
                                            "relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors "
                                            + (
                                                "bg-primary"
                                                if renabled
                                                else "bg-secondary"
                                            )
                                        )
                                        .on(
                                            "click",
                                            lambda _, n=rname, en=renabled: self._handle_toggle_rune(
                                                n, not en
                                            ),
                                        )
                                    ):
                                        ui.element("span").classes(
                                            "pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow transition "
                                            + (
                                                "translate-x-3"
                                                if renabled
                                                else "translate-x-0"
                                            )
                                        )

    # -------------------------------------------------------------------------
    # TAB 2: SKILLS & WIKISKILL EVOLUTION
    # -------------------------------------------------------------------------
    def _render_skills_tab(self) -> None:
        skills_list = self.ecosystem_data.get("skills", [])
        evolution = self.ecosystem_data.get("skill_evolution", {})

        with ui.element("div").classes("flex flex-col gap-6"):
            # WikiSkill Evolution Card
            with ui.element("div").classes(
                "p-4 rounded-xl border border-card-border bg-card flex flex-col gap-3"
            ):
                with ui.element("div").classes(
                    "flex flex-wrap items-center justify-between gap-2"
                ):
                    with ui.element("div").classes("flex items-center gap-2"):
                        AntigravityIcon("sparkles", size=16, classes="text-primary")
                        ui.label("WikiSkill Autonomous Evolution").classes(
                            "text-sm font-semibold text-foreground"
                        )
                        ui.label(
                            f"{evolution.get('traces_count', 0)} traces recorded"
                        ).classes(
                            "text-[10px] px-2 py-0.5 rounded-full bg-secondary text-muted-foreground border border-card-border"
                        )

                    with ui.element("div").classes("flex items-center gap-2"):
                        with (
                            ui.element("button")
                            .props('type="button"')
                            .classes(
                                "px-2.5 py-1 rounded-md text-xs font-medium bg-primary hover:bg-primary/90 text-primary-foreground cursor-pointer transition-colors"
                            )
                            .on("click", lambda _: self._handle_skill_evolution_consolidate())
                        ):
                            ui.label("Consolidate Experience")

                        with (
                            ui.element("button")
                            .props('type="button"')
                            .classes(
                                "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                            )
                            .on("click", lambda _: self._handle_skill_evolution_propose())
                        ):
                            ui.label("Propose Skills")

                # Learned Patterns
                patterns = evolution.get("patterns", [])
                if patterns:
                    with ui.element("div").classes(
                        "grid grid-cols-1 md:grid-cols-2 gap-2 mt-1"
                    ):
                        for pat in patterns:
                            with ui.element("div").classes(
                                "p-2.5 rounded-lg bg-secondary/40 border border-card-border/60 flex flex-col gap-1"
                            ):
                                ui.label(pat.get("title", pat.get("id", ""))).classes(
                                    "text-xs font-medium text-foreground"
                                )
                                ui.label(pat.get("summary", "")).classes(
                                    "text-[11px] text-muted-foreground line-clamp-2"
                                )

            # Skills Catalog
            with ui.element("div").classes("flex flex-col gap-3"):
                with ui.element("div").classes(
                    "flex flex-wrap items-center justify-between gap-2 px-1"
                ):
                    with ui.element("div").classes("flex items-center gap-2"):
                        ui.label(f"Active Skills ({len(skills_list)})").classes(
                            "text-xs font-semibold text-foreground uppercase tracking-wider"
                        )
                    with ui.element("div").classes("flex items-center gap-2"):
                        with (
                            ui.element("button")
                            .props('type="button"')
                            .classes(
                                "px-2.5 py-1 rounded-md text-xs bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer"
                            )
                            .on("click", lambda _: self._handle_dedupe_skills())
                        ):
                            ui.label("Deduplicate Shadowed")

                with ui.element("div").classes(
                    "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
                ):
                    if not skills_list:
                        with ui.element("div").classes(
                            "p-6 text-center text-xs text-muted-foreground"
                        ):
                            ui.label("No skills registered in this catalog.")
                    else:
                        for sk in skills_list:
                            sname = sk.get("name", "")
                            with ui.element("div").classes(
                                "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                            ):
                                with ui.element("div").classes(
                                    "flex flex-col gap-1 min-w-0 flex-1"
                                ):
                                    with ui.element("div").classes(
                                        "flex items-center gap-2"
                                    ):
                                        AntigravityIcon(
                                            "sparkles",
                                            size=13,
                                            classes="text-primary",
                                        )
                                        ui.label(sname).classes(
                                            "text-sm font-medium text-foreground truncate"
                                        )
                                        scope_val = sk.get("scope", "global")
                                        ui.label(scope_val).classes(
                                            "text-[10px] px-1.5 py-0.2 rounded border border-card-border bg-secondary text-muted-foreground uppercase"
                                        )
                                        for diag in sk.get("diagnostics", []):
                                            ui.label(diag).classes(
                                                "text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                            )
                                    ui.label(
                                        sk.get("description", "Agent skill definition.")
                                    ).classes("text-xs text-muted-foreground truncate")
                                    if sk.get("location"):
                                        ui.label(sk["location"]).classes(
                                            "text-[10px] font-mono text-muted-foreground/60 truncate"
                                        )

                                with ui.element("div").classes(
                                    "flex items-center gap-2 shrink-0"
                                ):
                                    with (
                                        ui.element("button")
                                        .props('type="button"')
                                        .classes(
                                            "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                                        )
                                        .on(
                                            "click",
                                            lambda _, s=sname: self._handle_activate_skill(
                                                s
                                            ),
                                        )
                                    ):
                                        ui.label("Activate")

    # -------------------------------------------------------------------------
    # TAB 3: STEERING (AGENTS.MD)
    # -------------------------------------------------------------------------
    def _render_steering_tab(self) -> None:
        steering_data = self.ecosystem_data.get("steering", {})
        proj_content = steering_data.get(
            "project_content", "# Project Steering Rules\nStrict TDD."
        )
        global_content = steering_data.get(
            "global_content", "# Global Steering Rules\nConcise technical prose."
        )
        subpkgs = steering_data.get("subpackages", [])

        with ui.element("div").classes("flex flex-col gap-5"):
            # Header actions
            with ui.element("div").classes(
                "flex flex-wrap items-center justify-between gap-3"
            ):
                with ui.element("div").classes("flex flex-col gap-0.5"):
                    ui.label("AGENTS.md Steering Hierarchy").classes(
                        "text-sm font-semibold text-foreground"
                    )
                    ui.label(
                        "Resolved layers: Global (~/.agents/AGENTS.md) -> Project (<cwd>/AGENTS.md) -> Subpackage pointers"
                    ).classes("text-xs text-muted-foreground")

                with (
                    ui.element("button")
                    .props('type="button"')
                    .classes(
                        "px-3 py-1.5 rounded-lg text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                    )
                    .on("click", lambda _: self._handle_validate_steering())
                ):
                    ui.label("Validate Steering (/steering validate)")

            # Project AGENTS.md Editor
            with ui.element("div").classes(
                "flex flex-col gap-2 p-4 rounded-xl border border-card-border bg-card"
            ):
                with ui.element("div").classes("flex items-center justify-between"):
                    ui.label("Project Layer (<cwd>/AGENTS.md)").classes(
                        "text-xs font-semibold text-foreground uppercase tracking-wider"
                    )
                    ui.label("Active Workspace").classes(
                        "text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20"
                    )

                proj_input = (
                    ui.textarea(value=proj_content)
                    .props("rows=6")
                    .classes(
                        "w-full text-xs font-mono bg-background border border-card-border rounded-lg p-2.5 text-foreground"
                    )
                )

                with ui.element("div").classes("flex justify-end"):
                    with (
                        ui.element("button")
                        .props('type="button"')
                        .classes(
                            "px-3 py-1 rounded-md text-xs font-medium bg-primary hover:bg-primary/90 text-primary-foreground cursor-pointer transition-colors"
                        )
                        .on(
                            "click",
                            lambda _, inp=proj_input: self._handle_save_steering(
                                "project", inp.value
                            ),
                        )
                    ):
                        ui.label("Save Project Rules")

            # Global AGENTS.md Editor
            with ui.element("div").classes(
                "flex flex-col gap-2 p-4 rounded-xl border border-card-border bg-card"
            ):
                with ui.element("div").classes("flex items-center justify-between"):
                    ui.label("Global Layer (~/.agents/AGENTS.md)").classes(
                        "text-xs font-semibold text-foreground uppercase tracking-wider"
                    )
                    ui.label("Cross-Project").classes(
                        "text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground border border-card-border"
                    )

                global_input = (
                    ui.textarea(value=global_content)
                    .props("rows=4")
                    .classes(
                        "w-full text-xs font-mono bg-background border border-card-border rounded-lg p-2.5 text-foreground"
                    )
                )

                with ui.element("div").classes("flex justify-end"):
                    with (
                        ui.element("button")
                        .props('type="button"')
                        .classes(
                            "px-3 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                        )
                        .on(
                            "click",
                            lambda _, inp=global_input: self._handle_save_steering(
                                "global", inp.value
                            ),
                        )
                    ):
                        ui.label("Save Global Rules")

            # Subpackage Pointers
            if subpkgs:
                with ui.element("div").classes(
                    "p-3.5 rounded-xl border border-card-border/60 bg-secondary/20 flex flex-col gap-1.5"
                ):
                    ui.label("Discovered Subpackage Pointers (Lazy-Read)").classes(
                        "text-xs font-medium text-foreground"
                    )
                    with ui.element("div").classes("flex flex-wrap gap-1.5"):
                        for pkg in subpkgs:
                            ui.label(pkg).classes(
                                "text-[11px] font-mono px-2 py-0.5 rounded bg-card text-muted-foreground border border-card-border"
                            )

    # -------------------------------------------------------------------------
    # TAB 4: MCP SERVERS
    # -------------------------------------------------------------------------
    def _render_mcp_tab(self) -> None:
        mcp_list = self.ecosystem_data.get("mcp_servers", [])

        with ui.element("div").classes("flex flex-col gap-6"):
            with ui.element("div").classes(
                "flex flex-wrap items-center justify-between gap-3"
            ):
                with ui.element("div").classes("flex flex-col gap-0.5"):
                    ui.label("Configured MCP Servers").classes(
                        "text-sm font-semibold text-foreground"
                    )
                    ui.label(
                        "Managed via ~/.agents/mcp.json and <cwd>/.agents/mcp.json. Connected on demand."
                    ).classes("text-xs text-muted-foreground")

            # Servers Table
            with ui.element("div").classes(
                "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
            ):
                if not mcp_list:
                    with ui.element("div").classes(
                        "p-6 text-center text-xs text-muted-foreground"
                    ):
                        ui.label("No MCP servers configured.")
                else:
                    for srv in mcp_list:
                        sname = srv.get("name", "")
                        disabled = srv.get("disabled", False)
                        connected = srv.get("connected", True)
                        with ui.element("div").classes(
                            "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                        ):
                            with ui.element("div").classes(
                                "flex flex-col gap-1 min-w-0 flex-1"
                            ):
                                with ui.element("div").classes(
                                    "flex items-center gap-2"
                                ):
                                    AntigravityIcon(
                                        "tune", size=13, classes="text-primary"
                                    )
                                    ui.label(sname).classes(
                                        "text-sm font-medium text-foreground truncate"
                                    )
                                    ui.label(
                                        srv.get("transport", "stdio")
                                    ).classes(
                                        "text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-muted-foreground border border-card-border uppercase"
                                    )
                                    status_cls = (
                                        "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                        if connected and not disabled
                                        else "bg-secondary text-muted-foreground border-card-border"
                                    )
                                    ui.label(
                                        "Connected"
                                        if (connected and not disabled)
                                        else "Disabled"
                                    ).classes(
                                        f"text-[10px] px-1.5 py-0.2 rounded border {status_cls}"
                                    )
                                ui.label(srv.get("command", "")).classes(
                                    "text-[11px] font-mono text-muted-foreground truncate"
                                )

                            with ui.element("div").classes(
                                "flex items-center gap-2 shrink-0"
                            ):
                                with (
                                    ui.element("button")
                                    .props('type="button"')
                                    .classes(
                                        "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                                    )
                                    .on(
                                        "click",
                                        lambda _, s=sname: self._handle_test_mcp(s),
                                    )
                                ):
                                    ui.label("Test Connection")

                                with (
                                    ui.element("button")
                                    .props('type="button" role="switch"')
                                    .classes(
                                        "relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors "
                                        + (
                                            "bg-secondary"
                                            if disabled
                                            else "bg-primary"
                                        )
                                    )
                                    .on(
                                        "click",
                                        lambda _, s=sname, d=disabled: self._handle_toggle_mcp(
                                            s, not d
                                        ),
                                    )
                                ):
                                    ui.element("span").classes(
                                        "pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow transition "
                                        + (
                                            "translate-x-0"
                                            if disabled
                                            else "translate-x-3"
                                        )
                                    )

    # -------------------------------------------------------------------------
    # TAB 5: OKF KNOWLEDGE GRAPH
    # -------------------------------------------------------------------------
    def _render_okf_tab(self) -> None:
        okf_data = self.ecosystem_data.get("okf", {})
        concepts = okf_data.get("concepts", [])
        used_tokens = okf_data.get("token_budget_used", 150)
        max_tokens = okf_data.get("token_budget_max", 2000)

        with ui.element("div").classes("flex flex-col gap-6"):
            # Token Budget & Actions Strip
            with ui.element("div").classes(
                "p-4 rounded-xl border border-card-border bg-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            ):
                with ui.element("div").classes("flex flex-col gap-1"):
                    with ui.element("div").classes("flex items-center gap-2"):
                        AntigravityIcon("folder", size=16, classes="text-primary")
                        ui.label("Open Knowledge Format (OKF v0.2)").classes(
                            "text-sm font-semibold text-foreground"
                        )
                    ui.label(
                        f"Context: Auto budget: {used_tokens:,} / {max_tokens:,} tokens allocated."
                    ).classes("text-xs text-muted-foreground")

                with (
                    ui.element("button")
                    .props('type="button"')
                    .classes(
                        "px-3 py-1.5 rounded-lg text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                    )
                    .on("click", lambda _: self._handle_okf_validate())
                ):
                    ui.label("Validate Bundle (/okf validate)")

            # Concepts Cards
            with ui.element("div").classes("flex flex-col gap-3"):
                ui.label(f"Concepts ({len(concepts)})").classes(
                    "text-xs font-semibold text-foreground uppercase tracking-wider px-1"
                )

                with ui.element("div").classes(
                    "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
                ):
                    if not concepts:
                        with ui.element("div").classes(
                            "p-6 text-center text-xs text-muted-foreground"
                        ):
                            ui.label("No OKF concepts indexed in this workspace.")
                    else:
                        for c in concepts:
                            cid = c.get("id", "")
                            trust = c.get("trust", "unverified")
                            with ui.element("div").classes(
                                "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                            ):
                                with ui.element("div").classes(
                                    "flex flex-col gap-1 min-w-0 flex-1"
                                ):
                                    with ui.element("div").classes(
                                        "flex flex-wrap items-center gap-2"
                                    ):
                                        ui.label(c.get("title", cid)).classes(
                                            "text-sm font-medium text-foreground"
                                        )
                                        ui.label(cid).classes(
                                            "text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-muted-foreground border border-card-border"
                                        )
                                        ui.label(
                                            c.get("type", "concept")
                                        ).classes(
                                            "text-[10px] px-1.5 py-0.2 rounded bg-secondary/80 text-secondary-foreground border border-card-border uppercase"
                                        )
                                        trust_cls = {
                                            "human-reviewed": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                                            "machine-confirmed": "bg-blue-500/10 text-blue-400 border-blue-500/20",
                                        }.get(
                                            trust,
                                            "bg-amber-500/10 text-amber-400 border-amber-500/20",
                                        )
                                        ui.label(trust).classes(
                                            f"text-[10px] px-1.5 py-0.2 rounded border {trust_cls}"
                                        )
                                    if c.get("cited_by"):
                                        ui.label(
                                            f"Cited by: {', '.join(c['cited_by'])}"
                                        ).classes(
                                            "text-[11px] font-mono text-muted-foreground"
                                        )

                                with ui.element("div").classes(
                                    "flex items-center gap-2 shrink-0"
                                ):
                                    if trust != "human-reviewed":
                                        with (
                                            ui.element("button")
                                            .props('type="button"')
                                            .classes(
                                                "px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 cursor-pointer transition-colors"
                                            )
                                            .on(
                                                "click",
                                                lambda _, i=cid: self._handle_verify_concept(
                                                    i
                                                ),
                                            )
                                        ):
                                            ui.label("Verify as Human")

    # -------------------------------------------------------------------------
    # TAB 6: ADRS (ARCHITECTURE DECISION RECORDS)
    # -------------------------------------------------------------------------
    def _render_adrs_tab(self) -> None:
        adrs_data = self.ecosystem_data.get("adrs", {})
        records = adrs_data.get("records", [])

        with ui.element("div").classes("flex flex-col gap-6"):
            with ui.element("div").classes(
                "flex flex-wrap items-center justify-between gap-3"
            ):
                with ui.element("div").classes("flex flex-col gap-0.5"):
                    ui.label("Architectural Decision Records (MADR 3.0)").classes(
                        "text-sm font-semibold text-foreground"
                    )
                    ui.label(
                        "Tracks architectural choices under docs/adr/####-slug.md"
                    ).classes("text-xs text-muted-foreground")

                with (
                    ui.element("button")
                    .props('type="button"')
                    .classes(
                        "px-3 py-1.5 rounded-lg text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                    )
                    .on("click", lambda _: self._handle_validate_adrs())
                ):
                    ui.label("Validate MADR 3.0 (/adr validate)")

            # ADRs List
            with ui.element("div").classes(
                "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
            ):
                if not records:
                    with ui.element("div").classes(
                        "p-6 text-center text-xs text-muted-foreground"
                    ):
                        ui.label("No ADR records found in docs/adr/.")
                else:
                    for adr in records:
                        num = adr.get("number", 0)
                        status = adr.get("status", "accepted")
                        with ui.element("div").classes(
                            "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                        ):
                            with ui.element("div").classes(
                                "flex flex-col gap-1 min-w-0 flex-1"
                            ):
                                with ui.element("div").classes(
                                    "flex items-center gap-2"
                                ):
                                    ui.label(f"ADR-{num:04d}").classes(
                                        "text-xs font-mono font-semibold text-foreground px-1.5 py-0.2 rounded bg-secondary border border-card-border"
                                    )
                                    ui.label(adr.get("title", "")).classes(
                                        "text-sm font-medium text-foreground truncate"
                                    )
                                    status_cls = {
                                        "accepted": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                                        "proposed": "bg-blue-500/10 text-blue-400 border-blue-500/20",
                                        "deprecated": "bg-rose-500/10 text-rose-400 border-rose-500/20",
                                    }.get(
                                        status,
                                        "bg-secondary text-muted-foreground border-card-border",
                                    )
                                    ui.label(status).classes(
                                        f"text-[10px] px-1.5 py-0.2 rounded border uppercase {status_cls}"
                                    )
                                ui.label(adr.get("path", "")).classes(
                                    "text-[11px] font-mono text-muted-foreground truncate"
                                )

    # -------------------------------------------------------------------------
    # TAB 7: SELF-MOD & SNAPSHOTS
    # -------------------------------------------------------------------------
    def _render_selfmod_tab(self) -> None:
        selfmod_data = self.ecosystem_data.get("selfmod", {})
        agent_name = selfmod_data.get("agent_name", "coding_mvge")
        config_dir = selfmod_data.get("config_dir", "")
        reload_needed = selfmod_data.get("reload_needed", False)
        snapshots = selfmod_data.get("snapshots", [])

        with ui.element("div").classes("flex flex-col gap-6"):
            # Hot-Reload Banner (if pending)
            if reload_needed:
                with ui.element("div").classes(
                    "p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 flex items-center justify-between gap-3"
                ):
                    with ui.element("div").classes("flex flex-col gap-0.5"):
                        ui.label(
                            "Extensions modified! Hot-reload candidate pending."
                        ).classes("text-sm font-medium text-amber-300")
                        ui.label(
                            "Runtime components changed on disk. Reload to activate new spells and sigils."
                        ).classes("text-xs text-amber-300/80")
                    with (
                        ui.element("button")
                        .props('type="button"')
                        .classes(
                            "px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500 text-black hover:bg-amber-400 cursor-pointer transition-colors"
                        )
                        .on("click", lambda _: self._handle_reload_mvge())
                    ):
                        ui.label("Reload Mvge Now (/reload)")

            # Agent & Paths Info Card
            with ui.element("div").classes(
                "p-4 rounded-xl border border-card-border bg-card flex flex-col gap-2"
            ):
                with ui.element("div").classes("flex items-center justify-between"):
                    ui.label("Active Mvge Configuration").classes(
                        "text-xs font-semibold text-foreground uppercase tracking-wider"
                    )
                    ui.label(agent_name).classes(
                        "text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-mono font-medium"
                    )
                if config_dir:
                    ui.label(f"Root: {config_dir}").classes(
                        "text-[11px] font-mono text-muted-foreground truncate"
                    )

            # Snapshots Timeline
            with ui.element("div").classes("flex flex-col gap-3"):
                with ui.element("div").classes(
                    "flex items-center justify-between px-1"
                ):
                    ui.label(f"Self-Mod Snapshots ({len(snapshots)})").classes(
                        "text-xs font-semibold text-foreground uppercase tracking-wider"
                    )
                    with (
                        ui.element("button")
                        .props('type="button"')
                        .classes(
                            "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                        )
                        .on("click", lambda _: self._handle_self_snapshot("manual"))
                    ):
                        ui.label("Create Snapshot")

                with ui.element("div").classes(
                    "border border-card-border rounded-xl overflow-hidden bg-card divide-y divide-border flex flex-col"
                ):
                    if not snapshots:
                        with ui.element("div").classes(
                            "p-6 text-center text-xs text-muted-foreground"
                        ):
                            ui.label("No snapshots taken yet.")
                    else:
                        for snap in snapshots:
                            sid = snap.get("id", "")
                            with ui.element("div").classes(
                                "flex items-center justify-between gap-3 px-4 py-3 hover:bg-secondary/30 transition-colors"
                            ):
                                with ui.element("div").classes(
                                    "flex flex-col gap-0.5 min-w-0 flex-1"
                                ):
                                    with ui.element("div").classes(
                                        "flex items-center gap-2"
                                    ):
                                        ui.label(sid).classes(
                                            "text-xs font-mono font-semibold text-foreground"
                                        )
                                        if snap.get("label"):
                                            ui.label(snap["label"]).classes(
                                                "text-[10px] px-1.5 py-0.2 rounded bg-secondary text-secondary-foreground border border-card-border"
                                            )
                                    ui.label(
                                        snap.get("timestamp", "recent")
                                    ).classes("text-[11px] text-muted-foreground")

                                with ui.element("div").classes(
                                    "flex items-center gap-2 shrink-0"
                                ):
                                    with (
                                        ui.element("button")
                                        .props('type="button"')
                                        .classes(
                                            "px-2.5 py-1 rounded-md text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground border border-card-border cursor-pointer transition-colors"
                                        )
                                        .on(
                                            "click",
                                            lambda _, s=sid: self._handle_rollback_snapshot(
                                                s
                                            ),
                                        )
                                    ):
                                        ui.label("Rollback")
