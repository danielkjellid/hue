"""
A props table lists what is particular to its component, read off the class.
"""

from __future__ import annotations

from hue.ui import Button, TextInput

from hue_docs_v2.props import props_of


def _by_name(cls):
    return {prop.name: prop for prop in props_of(cls)}


def test_the_shared_modifiers_are_left_out() -> None:
    names = _by_name(Button)
    for shared in ("class_", "id", "aria_label", "x_on", "on_click", "form", "content"):
        assert shared not in names


def test_a_literal_alias_is_spelled_out() -> None:
    assert "'xs' | 'sm' | 'md' | 'lg'" in _by_name(Button)["size"].signature


def test_the_default_is_read_from_render() -> None:
    assert _by_name(Button)["variant"].default == "'primary'"


def test_a_long_literal_is_cut_short() -> None:
    assert "more" in _by_name(TextInput)["autocomplete"].signature


def test_what_a_base_form_control_adds_is_listed() -> None:
    names = _by_name(TextInput)
    assert {"name", "label", "error", "hint"} <= names.keys()


def test_the_docstring_s_first_paragraph_is_the_description() -> None:
    assert _by_name(Button)["pill"].doc.startswith("Round the ends fully")
