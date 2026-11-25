"""Tests for header module."""

from nicegui_ai.header import FloatingHeader, TokenRing


def test_token_ring_init():
    ring = TokenRing(used=25000, limit=100000)
    assert ring.used == 25000
    assert ring.limit == 100000


def test_token_ring_update():
    ring = TokenRing(used=10, limit=100)
    ring.update_progress(50, 100)
    assert ring.used == 50
    assert ring.limit == 100


def test_floating_header_init():
    header = FloatingHeader(
        agent_name="TestAgent",
        model="gpt-4o",
        tokens_used=1000,
        token_limit=10000,
    )
    assert header.token_ring.used == 1000
    header.update_tokens(2500)
    assert header.token_ring.used == 2500
