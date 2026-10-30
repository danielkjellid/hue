"""
The two rendering helpers, and the line between them.

They exist so every optional child in the system reads the same way. The
split matters because reaching for the wrong one still compiles: render_if
tests against None, so handing it a False renders the thing you meant to
hide.
"""

import pytest
from htmy import html

from hue.types.core import UNDEFINED
from hue.utils import render_if, render_when


class TestRenderIf:
    @pytest.mark.parametrize("value", ["Title", False, 0, "", ()])
    def test_anything_but_none_is_a_value(self, value):
        # Which is the whole reason render_when exists: a flag handed to this
        # one renders, because False is not None.
        assert render_if(value, lambda _: html.span("x")) is not UNDEFINED

    def test_none_renders_the_fallback(self):
        fallback = html.span("none")
        assert render_if(None, lambda _: html.span("x")) is UNDEFINED
        assert render_if(None, lambda _: html.span("x"), fallback) is fallback


class TestRenderWhen:
    def test_renders_when_true(self):
        marker = html.span("x")
        assert render_when(True, marker) is marker

    def test_false_renders_the_fallback(self):
        # It takes the component, not a factory: there is no value to hand
        # along, so a callback would be a lambda of no arguments everywhere.
        fallback = html.span("y")
        assert render_when(False, html.span("x")) is UNDEFINED
        assert render_when(False, html.span("x"), fallback) is fallback
