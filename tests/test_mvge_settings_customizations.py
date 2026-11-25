"""Hermetic tests for Mvge SettingsModal sections and WorkspaceCustomizationsView ecosystem tabs."""

from typing import Any

from nicegui_ai.antigravity import (
    PersonaConfig,
    SettingsModal,
    WorkspaceCustomizationsView,
    create_default_settings,
    create_default_skills,
)


def test_mvge_settings_modal_realms_and_approval() -> None:
    settings = create_default_settings()
    skills = create_default_skills()
    actions: list[tuple[str, dict[str, Any]]] = []

    def on_action(action: str, payload: dict[str, Any]) -> None:
        actions.append((action, payload))

    mvge_data = {
        "realms": [
            {
                "id": "opencode",
                "name": "OpenCode",
                "base_url": "https://opencode.ai/inference/openai/v1",
                "env_var": "OPENCODE_API_KEY",
                "is_router": False,
                "has_key": True,
                "masked_key": "oc_sk_...yU",
                "default_model": "opencode/big-pickle",
                "keyless_models": ["opencode/big-pickle", "opencode/space-bunny-free"],
                "rune_installed": True,
                "rune_name": "opencode-realm",
            },
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "base_url": "https://openrouter.ai/api/v1",
                "env_var": "OPENROUTER_API_KEY",
                "is_router": True,
                "has_key": False,
                "masked_key": "",
                "default_model": "openrouter/free",
                "keyless_models": [],
                "rune_installed": True,
                "rune_name": "openrouter-realm",
            },
        ],
        "approval": {
            "session": {"session_id": "tome-test-1", "approve_all_active": False},
            "trusted_projects": [
                {"id": "tp-1", "root": "/mnt/storage/projects/mvge", "enabled": True}
            ],
            "always_allowed": [
                {
                    "id": "grant-1",
                    "spell": "read",
                    "scope_label": "Project",
                    "constraint_labels": ["path_within_project"],
                }
            ],
            "never_allowed": [
                {
                    "id": "grant-deny-1",
                    "spell": "dangerous_spell",
                    "scope_label": "Global",
                }
            ],
            "recent_activity": [
                {
                    "spell": "bash",
                    "outcome": "completed",
                    "timestamp": "12:00:00",
                    "reason_code": "read_only",
                }
            ],
            "warnings": ["Integrity notice: 1 grant shadowed."],
        },
        "trust": {
            "workspace": "/mnt/storage/projects/mvge",
            "status": "trusted",
            "fingerprint": "a1b2c3d4e5f6",
            "has_project_extensions": True,
        },
        "compaction": {
            "enabled": True,
            "reserve_mana": 16384,
            "keep_recent_mana": 8192,
            "context_window": 128000,
            "threshold": 0.85,
            "current_mana_used": 24500,
        },
        "diagnostics": {
            "mvge_version": "0.3.0",
            "active_mvge": "coding_mvge",
            "active_profile": "coding",
            "checks": [{"name": "ripgrep", "ok": True, "detail": "rg 14.1.0"}],
            "otel": {"enabled": False},
            "mcp_summary": {"connected": 2, "disabled": 0},
        },
    }

    modal = SettingsModal(
        is_open=True,
        initial_screen="realms",
        settings=settings,
        skills=skills,
        persona=PersonaConfig(app_name="Mvge"),
        mvge_data=mvge_data,
        on_mvge_action=on_action,
    )

    assert modal.active_screen == "realms"
    modal._handle_save_realm_key("opencode", "oc_sk_new_key_123")
    assert actions[-1] == (
        "save_realm_key",
        {"realm": "opencode", "api_key": "oc_sk_new_key_123"},
    )

    modal._handle_clear_realm_key("opencode")
    assert actions[-1] == ("clear_realm_key", {"realm": "opencode"})

    modal.set_screen("approval")
    assert modal.active_screen == "approval"
    modal._handle_toggle_session_approve_all(True)
    assert actions[-1] == ("toggle_session_approve_all", {"enabled": True})

    modal._handle_revoke_grant("allow_rule", "grant-1")
    assert actions[-1] == (
        "revoke_grant",
        {"kind": "allow_rule", "grant_id": "grant-1"},
    )

    modal.set_screen("trust")
    assert modal.active_screen == "trust"
    modal._handle_set_workspace_trust(True)
    assert actions[-1] == ("set_workspace_trust", {"trusted": True})

    modal.set_screen("compaction")
    assert modal.active_screen == "compaction"
    modal._handle_compact_now()
    assert actions[-1] == ("compact_now", {})


def test_workspace_customizations_view_ecosystem_tabs() -> None:
    settings = create_default_settings()
    actions: list[tuple[str, dict[str, Any]]] = []

    def on_action(action: str, payload: dict[str, Any]) -> None:
        actions.append((action, payload))

    eco_data = {
        "profiles": {
            "active": "coding",
            "available": [
                {"name": "minimal", "count": 4, "desc": "Lightweight"},
                {"name": "coding", "count": 12, "desc": "Flagship"},
                {"name": "autonomous", "count": 19, "desc": "Full Stack"},
            ],
        },
        "runes": [
            {
                "name": "approval-rune",
                "version": "0.1.0",
                "description": "Fail-closed gate",
                "profile": "minimal",
                "types": ["Spell Gate"],
                "enabled": True,
                "has_settings": False,
            }
        ],
        "skills": [
            {
                "name": "git-workflow",
                "description": "Automated git commit",
                "scope": "project",
                "location": "/path/SKILL.md",
                "resources_count": 2,
                "diagnostics": [],
            }
        ],
        "skill_evolution": {
            "traces_count": 42,
            "patterns": [
                {
                    "id": "pat-1",
                    "title": "Error Handling in Bash",
                    "summary": "Use tail accumulator",
                }
            ],
            "impact_log": "+ added skill bash-guard",
        },
        "steering": {
            "global_content": "# Global Rules\nConcise technical prose.",
            "project_content": "# Project Rules\nStrict TDD.",
            "subpackages": ["packages/core", "packages/desktop"],
        },
        "mcp_servers": [
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": "npx -y @modelcontextprotocol/server-filesystem",
                "disabled": False,
                "connected": True,
            }
        ],
        "okf": {
            "concepts": [
                {
                    "id": "mana-pool",
                    "title": "Mana Pool Context",
                    "type": "architecture",
                    "trust": "human-reviewed",
                    "stale": False,
                    "context": "auto",
                    "cited_by": ["adr-0010"],
                    "tags": ["core", "mana"],
                }
            ],
            "token_budget_used": 150,
            "token_budget_max": 2000,
        },
        "adrs": {
            "records": [
                {
                    "number": 1,
                    "title": "Adopt ADR-0001",
                    "status": "accepted",
                    "date": "2026-01-01",
                    "deciders": "Summoner",
                    "path": "docs/adr/0001-adopt.md",
                }
            ],
            "valid": True,
            "errors": [],
        },
        "selfmod": {
            "agent_name": "coding_mvge",
            "config_dir": "/home/vanluther/.agents/agents/coding_mvge",
            "reload_needed": False,
            "snapshots": [
                {"id": "snap-1", "timestamp": "2026-11-05 12:00", "label": "pre-edit"}
            ],
        },
    }

    cv = WorkspaceCustomizationsView(
        projects=settings.projects,
        active_project_id="proj-mvge",
        persona=PersonaConfig(app_name="Mvge"),
        initial_tab="runes",
        ecosystem_data=eco_data,
        on_ecosystem_action=on_action,
    )

    assert cv.active_tab == "runes"
    cv._handle_apply_profile("autonomous")
    assert actions[-1] == ("apply_profile", {"profile": "autonomous"})

    cv.set_tab("skills")
    assert cv.active_tab == "skills"
    cv._handle_activate_skill("git-workflow")
    assert actions[-1] == ("activate_skill", {"name": "git-workflow"})

    cv.set_tab("steering")
    assert cv.active_tab == "steering"
    cv._handle_save_steering("project", "# Project Updated")
    assert actions[-1] == (
        "save_steering",
        {"scope": "project", "content": "# Project Updated"},
    )

    cv.set_tab("mcp")
    assert cv.active_tab == "mcp"
    cv._handle_test_mcp("filesystem")
    assert actions[-1] == ("test_mcp_server", {"name": "filesystem"})

    cv.set_tab("okf")
    assert cv.active_tab == "okf"
    cv._handle_verify_concept("mana-pool")
    assert actions[-1] == ("okf_verify", {"concept_id": "mana-pool"})

    cv.set_tab("adrs")
    assert cv.active_tab == "adrs"
    cv._handle_validate_adrs()
    assert actions[-1] == ("adr_validate", {})

    cv.set_tab("selfmod")
    assert cv.active_tab == "selfmod"
    cv._handle_rollback_snapshot("snap-1")
    assert actions[-1] == ("self_rollback", {"snapshot_id": "snap-1"})
