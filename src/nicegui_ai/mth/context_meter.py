"""Context occupancy meter and detailed breakdown modal dialog for token capacity."""

import math

from nicegui import ui

from .state import MthContextOccupancy, format_tokens


class MthContextBreakdownDialog(ui.dialog):
    """Modal dialog displaying heuristic context breakdown by source category."""

    def __init__(self, occupancy: MthContextOccupancy) -> None:
        super().__init__()
        self.occupancy = occupancy
        self._build_ui()

    def _build_ui(self) -> None:
        with (
            self,
            ui.card().classes(
                "w-[380px] bg-[#141722] border border-[#262c3d] p-5 rounded-2xl shadow-2xl flex flex-col gap-4 text-slate-100"
            ),
        ):
            # Header
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("donut_large", size="18px").classes("text-blue-400")
                    ui.label("Context Occupancy").classes(
                        "text-sm font-semibold tracking-tight text-white"
                    )
                ui.button(
                    icon="close",
                    on_click=self.close,
                ).props("dense flat round size=sm").classes(
                    "text-slate-400 hover:text-white"
                )

            # Usage metric headline
            used = self.occupancy.used_tokens
            cap = self.occupancy.context_window
            pct = self.occupancy.percent()

            with ui.row().classes("w-full items-baseline justify-between"):
                with ui.row().classes("items-baseline gap-1.5"):
                    ui.label(f"{pct}%").classes(
                        "text-2xl font-bold font-mono text-white"
                    )
                    ui.label("used").classes("text-xs text-slate-400")
                ui.label(f"~{format_tokens(used)} / {format_tokens(cap)}").classes(
                    "text-xs font-mono text-slate-400"
                )

            # Segmented progress bar
            # Avoid divide-by-zero
            total_cat = (
                self.occupancy.system_tokens
                + self.occupancy.tools_tokens
                + self.occupancy.message_tokens
            )
            if total_cat > 0:
                sys_w = (self.occupancy.system_tokens / cap) * 100.0
                tools_w = (self.occupancy.tools_tokens / cap) * 100.0
                msg_w = (self.occupancy.message_tokens / cap) * 100.0
            else:
                sys_w = 0.0
                tools_w = 0.0
                msg_w = pct

            with ui.row().classes(
                "w-full h-2.5 bg-[#1f2533] rounded-full overflow-hidden gap-0.5 p-0.5"
            ):
                if sys_w > 0:
                    ui.element("div").classes("h-full bg-blue-500 rounded-sm").style(
                        f"width: {sys_w:.1f}%;"
                    )
                if tools_w > 0:
                    ui.element("div").classes("h-full bg-amber-500 rounded-sm").style(
                        f"width: {tools_w:.1f}%;"
                    )
                if msg_w > 0:
                    ui.element("div").classes("h-full bg-emerald-500 rounded-sm").style(
                        f"width: {msg_w:.1f}%;"
                    )

            # Legend details list
            with ui.column().classes("w-full gap-2 pt-1 font-sans text-xs"):
                self._render_legend_row(
                    color_class="bg-blue-500",
                    label="System Prompt",
                    tokens=self.occupancy.system_tokens,
                )
                self._render_legend_row(
                    color_class="bg-amber-500",
                    label="Tool Schemas",
                    tokens=self.occupancy.tools_tokens,
                )
                self._render_legend_row(
                    color_class="bg-emerald-500",
                    label="Conversation History",
                    tokens=self.occupancy.message_tokens,
                )

                free_tokens = max(0, cap - used)
                self._render_legend_row(
                    color_class="bg-slate-600",
                    label="Available Capacity",
                    tokens=free_tokens,
                )

            # Footer close button
            with ui.row().classes("w-full justify-end pt-2 border-t border-[#232736]"):
                ui.button("Done", on_click=self.close).props(
                    "dense no-caps flat size=sm"
                ).classes("text-slate-300 hover:text-white px-3")

    def _render_legend_row(self, color_class: str, label: str, tokens: int) -> None:
        with ui.row().classes("w-full items-center justify-between text-xs"):
            with ui.row().classes("items-center gap-2"):
                ui.element("span").classes(f"w-2.5 h-2.5 rounded-full {color_class}")
                ui.label(label).classes("text-slate-300")
            ui.label(f"~{format_tokens(tokens)}").classes("font-mono text-slate-400")


class MthContextMeter(ui.button):
    """Circular ring token meter trigger embedded in the composer dock."""

    def __init__(self, occupancy: MthContextOccupancy | None = None) -> None:
        super().__init__()
        self.occupancy = occupancy or MthContextOccupancy()
        self.props("dense flat no-caps size=xs").classes(
            "p-1 hover:bg-[#1b202c] rounded-md transition-colors"
        )
        self.on_click(self.open_dialog)
        self._build_ui()

    def _build_ui(self) -> None:
        self.clear()
        pct = self.occupancy.percent()
        radius = 5.5
        circ = 2 * math.pi * radius
        fill_dash = (circ * pct) / 100.0

        ring_color = "#3b82f6"
        if pct >= 90:
            ring_color = "#ef4444"
        elif pct >= 75:
            ring_color = "#f59e0b"

        with self:
            with ui.row().classes("items-center gap-1.5"):
                # 14px Circular SVG Gauge
                svg_html = (
                    f'<svg viewBox="0 0 14 14" width="14" height="14" class="block shrink-0">'
                    f'<circle cx="7" cy="7" r="{radius}" stroke="#2b3144" stroke-width="2" fill="none" />'
                    f'<circle cx="7" cy="7" r="{radius}" stroke="{ring_color}" stroke-width="2" fill="none" '
                    f'stroke-dasharray="{fill_dash:.2f} {circ:.2f}" transform="rotate(-90 7 7)" />'
                    f"</svg>"
                )
                ui.html(svg_html)
                self.pct_label = ui.label(f"{pct:.0f}%").classes(
                    "text-[11px] font-mono text-slate-400"
                )

            self.tooltip(
                f"{pct}% of context used (~{format_tokens(self.occupancy.used_tokens)} / {format_tokens(self.occupancy.context_window)})"
            )

    def set_occupancy(self, occupancy: MthContextOccupancy) -> None:
        """Update context occupancy and refresh gauge visuals."""
        self.occupancy = occupancy
        self._build_ui()

    def open_dialog(self) -> None:
        """Open detailed breakdown dialog."""
        dialog = MthContextBreakdownDialog(occupancy=self.occupancy)
        dialog.open()
