"""MTH visual styling tokens, CSS variables, and layout setup."""

from nicegui import ui

MTH_THEME_CSS = """
:root {
  --mth-bg: #090a0f;
  --mth-surface: #11131a;
  --mth-card: #151822;
  --mth-card-hover: #1c202e;
  --mth-border: #232736;
  --mth-primary: #3b82f6;
  --mth-primary-hover: #2563eb;
  --mth-accent: #8b5cf6;
  --mth-amber: #f59e0b;
  --mth-emerald: #10b981;
  --mth-rose: #f43f5e;
  --mth-text-main: #f1f5f9;
  --mth-text-muted: #94a3b8;
  --mth-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --mth-font-sans: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

body {
  background-color: var(--mth-bg) !important;
  color: var(--mth-text-main) !important;
  font-family: var(--mth-font-sans) !important;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.mth-font-mono {
  font-family: var(--mth-font-mono) !important;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--mth-border);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--mth-text-muted);
}

/* Quasar resets */
.q-btn {
  text-transform: none !important;
  letter-spacing: normal !important;
}
.q-focus-helper {
  display: none !important;
}
"""


def setup_mth_theme() -> None:
    """Inject MTH theme styles and configure dark mode."""
    ui.dark_mode().enable()
    ui.add_head_html(f"<style>{MTH_THEME_CSS}</style>")
