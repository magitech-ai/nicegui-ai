# Context Map

## Contexts

- [Assistant-UI Primitives](./CONTEXT.md) — ambient glassmorphic AI chat, reasoning, tool execution, and streaming primitives (`nicegui_ai`)
- [Antigravity Desktop Clone](./src/nicegui_ai/antigravity/CONTEXT.md) — 1:1 desktop UI/UX clone of Google Antigravity built in Python and NiceGUI (`nicegui_ai.antigravity`)
- [Magitech Harness UI](./src/nicegui_ai/mth/CONTEXT.md) — 1:1 desktop and web interface for the Magitech Harness runtime substrate powered by the Anima micro-kernel (`nicegui_ai.mth`)

## Relationships

- **Assistant-UI Primitives → Antigravity Desktop Clone**: `nicegui_ai.antigravity` consumes `BaseStreamAdapter`, `GeminiStreamAdapter`, `OpenRouterStreamAdapter`, and `OpenCodeStreamAdapter` (`nicegui_ai.adapters`) to stream normalized AG-UI events into Antigravity conversation turns.
- **Assistant-UI Primitives → Magitech Harness UI**: `nicegui_ai.mth` leverages core primitives (`TokenRing`, `ReasoningCard`, `ToolCallCard`, `CodeBlock`, `ArtifactViewerDrawer`) while implementing specialized harness turn flows, tool-pairing verification, approval gates, and session drawers.
- **Assistant-UI Primitives ↔ Antigravity Desktop Clone ↔ Magitech Harness UI**: All three contexts coexist inside the `nicegui-ai` package with isolated theme tokens and layout models.
