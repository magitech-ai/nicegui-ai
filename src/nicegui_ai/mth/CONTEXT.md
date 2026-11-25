# Magitech Harness Desktop & Web UI (`nicegui_ai.mth`)

Modern, reactive user interface primitives for the Magitech Harness runtime substrate powered by the Anima micro-kernel and NiceGUI.

## Shell & Navigation

**Harness Window**:
The root desktop or web application shell orchestrating session navigation, turn execution, and artifact inspection.
_Avoid_: App container, main window, dashboard

**Session Drawer**:
The collapsible left navigation drawer displaying persistent session history, session creation, profile switching, and search.
_Avoid_: Sidebar, left panel, chat history drawer

**Top Bar**:
The persistent header displaying harness identity, current profile, active session name, and context token pressure.
_Avoid_: Navbar, header strip, status bar

**Inspector Drawer**:
The off-canvas right drawer for deep inspection of tool executions, session event logs, workspace diffs, and generated artifacts.
_Avoid_: Side panel, debug drawer, aux pane

## Conversation & Timeline

**Timeline**:
The chronological stream of conversation turns displaying user inputs, deliberation steps, tool cards, and assistant prose.
_Avoid_: Chat feed, message log, thread container

**Turn Card**:
A discrete conversational block encapsulating a single user directive, model deliberation, tool invocations, and final completion.
_Avoid_: Message row, chat bubble, interaction block

**Deliberation Card**:
A collapsible thought container displaying the model's internal chain-of-thought, reflection steps, and elapsed deliberation time.
_Avoid_: Reasoning block, scratchpad, thinking card

**Tool Card**:
A high-visibility card rendering the active lifecycle of an agent tool call (`pending`, `executing`, `completed`, `failed`), parameter diffs, and execution results.
_Avoid_: Action widget, function box, tool output

**Approval Gate**:
An interactive human-in-the-loop authorization barrier within a tool card requiring explicit user confirmation before sensitive operations execute.
_Avoid_: Permission modal, confirmation prompt, veto gate

## Composer & Input

**Composer**:
The anchored bottom dock where users input prompts, dispatch slash commands, select execution profiles, and trigger cancellation.
_Avoid_: Input bar, prompt box, text input

**Action Button**:
The multi-state button within the composer toggling between `Send`, `Stop` (cooperative cancellation via `AbortSignal`), and `Queue`.
_Avoid_: Submit button, send icon

**Fastpick Popover**:
The autocomplete dropdown triggered when authoring `/` directives or `@` workspace file references in the composer.
_Avoid_: Command palette, slash menu, dropdown

**Token Ring**:
The circular progress meter tracking session context consumption against the active profile's token limit.
_Avoid_: Context gauge, token meter, pie progress
