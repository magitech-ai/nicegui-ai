"""Composer statistics pills displaying activity and token usage metrics."""

from nicegui import ui

from .state import MthSessionStats


def format_duration(ms: float) -> str:
    """Format duration in milliseconds to human readable compact time."""
    if ms <= 0:
        return "0.0s"
    s = ms / 1000.0
    if s < 60:
        return f"{s:.1f}s"
    m = int(s // 60)
    rem_s = int(s % 60)
    return f"{m}m {rem_s}s"


class MthStatsPills(ui.row):
    """Pills bar docked above composer displaying real-time speed, latency, and token statistics."""

    def __init__(self, metrics: MthSessionStats | None = None) -> None:
        super().__init__()
        self.metrics = metrics or MthSessionStats()
        self.classes(
            "w-full items-center justify-between px-2 py-1 text-xs select-none"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            with ui.row().classes("items-center gap-2"):
                # 1. Activity Pill (Speed, Turns, Steps, Time)
                self.activity_pill = (
                    ui.button(on_click=self._show_activity_dialog)
                    .props("dense flat no-caps size=sm")
                    .classes(
                        "text-slate-400 hover:text-slate-200 bg-[#161922] hover:bg-[#1f2430] border border-[#262b3a] rounded-full px-2.5 py-0.5 flex items-center gap-1.5"
                    )
                )
                with self.activity_pill:
                    ui.icon("speed", size="14px").classes("text-blue-400")
                    self.activity_label = ui.label("0.0 tok/s").classes(
                        "font-mono text-[11px]"
                    )

                # 2. Usage Pill (Tokens, Cache Hit)
                self.usage_pill = (
                    ui.button(on_click=self._show_usage_dialog)
                    .props("dense flat no-caps size=sm")
                    .classes(
                        "text-slate-400 hover:text-slate-200 bg-[#161922] hover:bg-[#1f2430] border border-[#262b3a] rounded-full px-2.5 py-0.5 flex items-center gap-1.5"
                    )
                )
                with self.usage_pill:
                    ui.icon("storage", size="14px").classes("text-emerald-400")
                    self.usage_label = ui.label("0 tokens").classes(
                        "font-mono text-[11px]"
                    )

            self._refresh_labels()

    def _refresh_labels(self) -> None:
        # Activity
        tps = self.metrics.tokens_per_second()
        speed_str = f"{tps:.1f} tok/s" if tps > 0 else "0.0 tok/s"
        if self.metrics.steps > 0:
            act_text = (
                f"Turn {self.metrics.turns} · Step {self.metrics.steps} · {speed_str}"
            )
        else:
            act_text = speed_str
        self.activity_label.set_text(act_text)

        # Usage
        total = self.metrics.total_tokens()
        cache_hit = self.metrics.cache_hit_percent()
        if cache_hit is not None:
            usage_text = f"{total:,} tokens · Cache {cache_hit}%"
        else:
            usage_text = f"{total:,} tokens"
        self.usage_label.set_text(usage_text)

    def update_metrics(self, metrics: MthSessionStats) -> None:
        """Update metrics and refresh UI labels."""
        self.metrics = metrics
        self._refresh_labels()

    def _show_activity_dialog(self) -> None:
        """Open detailed timing, latency and speed breakdown dialog."""
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
                    ui.icon("speed", size="18px").classes("text-blue-400")
                    ui.label("Session Activity & Timing").classes(
                        "font-semibold text-sm text-white"
                    )
                ui.button(icon="close", on_click=dialog.close).props(
                    "dense flat round size=sm"
                )

            tps = self.metrics.tokens_per_second()
            ttft_avg = (
                self.metrics.ttft_ms / self.metrics.ttft_steps
                if self.metrics.ttft_steps > 0
                else 0.0
            )

            with ui.column().classes("w-full gap-2 text-xs font-mono"):
                self._render_metric_row(
                    "Decoding Speed", f"{tps:.1f} tok/s", "text-blue-400"
                )
                self._render_metric_row(
                    "LLM Wall Time", format_duration(self.metrics.llm_ms)
                )
                self._render_metric_row(
                    "Tool Execution Time", format_duration(self.metrics.tool_ms)
                )
                self._render_metric_row("TTFT Latency", format_duration(ttft_avg))
                self._render_metric_row("Total Turns", str(self.metrics.turns))
                self._render_metric_row("Total Steps", str(self.metrics.steps))

        dialog.open()

    def _show_usage_dialog(self) -> None:
        """Open detailed token consumption and cache hit breakdown dialog."""
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
                    ui.icon("storage", size="18px").classes("text-emerald-400")
                    ui.label("Session Token Accounting").classes(
                        "font-semibold text-sm text-white"
                    )
                ui.button(icon="close", on_click=dialog.close).props(
                    "dense flat round size=sm"
                )

            cache_hit = self.metrics.cache_hit_percent()
            cache_hit_str = f"{cache_hit}%" if cache_hit is not None else "N/A"

            with ui.column().classes("w-full gap-2 text-xs font-mono"):
                self._render_metric_row(
                    "Total Tokens",
                    f"{self.metrics.total_tokens():,}",
                    "text-emerald-400",
                )
                self._render_metric_row(
                    "Cache Hit Ratio", cache_hit_str, "text-emerald-300"
                )
                self._render_metric_row(
                    "Uncached Input", f"{self.metrics.uncached_input_tokens:,}"
                )
                self._render_metric_row(
                    "Cache Read", f"{self.metrics.cache_read_tokens:,}"
                )
                self._render_metric_row(
                    "Cache Write", f"{self.metrics.cache_write_tokens:,}"
                )
                self._render_metric_row(
                    "Generated Output", f"{self.metrics.output_tokens:,}"
                )

        dialog.open()

    def _render_metric_row(
        self, label: str, value: str, value_class: str = "text-slate-200"
    ) -> None:
        with ui.row().classes(
            "w-full justify-between items-center py-1 border-b border-[#1c202e]"
        ):
            ui.label(label).classes("text-slate-400")
            ui.label(value).classes(f"font-semibold {value_class}")
