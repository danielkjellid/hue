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
    def test_renders_the_value(self):
        assert render_if("Title", lambda text: html.h2(text)) is not UNDEFINED

    def test_nothing_for_none(self):
        assert render_if(None, lambda text: html.h2(text)) is UNDEFINED

    @pytest.mark.parametrize("value", [False, 0, "", ()])
    def test_falsy_is_still_a_value(self, value):
        # Which is the whole reason render_when exists: a flag handed to this
        # one renders, because False is not None.
        assert render_if(value, lambda _: html.span("x")) is not UNDEFINED

    def test_the_fallback_replaces_it(self):
        fallback = html.span("none")
        assert render_if(None, lambda _: html.span("x"), fallback) is fallback


class TestRenderWhen:
    def test_renders_when_true(self):
        marker = html.span("x")
        assert render_when(True, marker) is marker

    def test_nothing_when_false(self):
        assert render_when(False, html.span("x")) is UNDEFINED

    def test_it_takes_the_component_not_a_factory(self):
        # There is no value to hand along, so a callback would be a lambda of
        # no arguments at every call site. The component is built either way;
        # the one that turns out unused is an element nobody walks.
        assert render_when(False, html.span("x"), html.span("y")) is not UNDEFINED

    def test_an_empty_collection_is_a_condition(self):
        assert render_when(bool([]), html.span("x")) is UNDEFINED
        assert render_when(bool(["a"]), html.span("x")) is not UNDEFINED
