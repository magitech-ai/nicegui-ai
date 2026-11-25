"""Adapter normalizing streaming harness events into reactive UI signals."""

import asyncio
from collections.abc import Callable
from typing import Any


class MthStreamAdapter:
    """Consumes asynchronous generator events from Magitech Harness and emits UI signals."""

    def __init__(self) -> None:
        self._token_listeners: list[Callable[[str], Any]] = []
        self._reasoning_listeners: list[Callable[[str], Any]] = []
        self._tool_call_listeners: list[Callable[[str, str, dict[str, Any]], Any]] = []
        self._tool_resolved_listeners: list[Callable[[str, str], Any]] = []
        self._turn_complete_listeners: list[Callable[[], Any]] = []

    def on_token(self, callback: Callable[[str], Any]) -> None:
        """Register a callback for text token deltas."""
        self._token_listeners.append(callback)

    def on_reasoning(self, callback: Callable[[str], Any]) -> None:
        """Register a callback for deliberation thoughts."""
        self._reasoning_listeners.append(callback)

    def on_tool_call(self, callback: Callable[[str, str, dict[str, Any]], Any]) -> None:
        """Register a callback when a tool invocation begins."""
        self._tool_call_listeners.append(callback)

    def on_tool_resolved(self, callback: Callable[[str, str], Any]) -> None:
        """Register a callback when a tool resolution finishes."""
        self._tool_resolved_listeners.append(callback)

    def on_turn_complete(self, callback: Callable[[], Any]) -> None:
        """Register a callback when the full turn completes."""
        self._turn_complete_listeners.append(callback)

    async def feed_token(self, token: str) -> None:
        """Dispatch a streamed token chunk."""
        for listener in self._token_listeners:
            res = listener(token)
            if asyncio.iscoroutine(res):
                await res

    async def feed_reasoning(self, thought: str) -> None:
        """Dispatch a deliberation thought fragment."""
        for listener in self._reasoning_listeners:
            res = listener(thought)
            if asyncio.iscoroutine(res):
                await res

    async def feed_tool_call(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> None:
        """Dispatch a tool invocation notice."""
        for listener in self._tool_call_listeners:
            res = listener(call_id, name, args)
            if asyncio.iscoroutine(res):
                await res

    async def feed_tool_resolution(self, name: str, result: str) -> None:
        """Dispatch a tool resolution notice."""
        for listener in self._tool_resolved_listeners:
            res = listener(name, result)
            if asyncio.iscoroutine(res):
                await res

    async def feed_turn_complete(self) -> None:
        """Dispatch a turn completion notice."""
        for listener in self._turn_complete_listeners:
            res = listener()
            if asyncio.iscoroutine(res):
                await res
