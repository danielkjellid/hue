"""
A props table lists what is particular to its component, read off the class.
"""

from __future__ import annotations

from hue.ui import Button, Empty, PasswordInput, TextInput

from hue_docs.props import props_of


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


def test_a_default_is_read_from_the_render_a_subclass_overrides() -> None:
    # PasswordInput's own _render reads only revealable; size is read in the
    # base's _render, which it calls through super().
    names = _by_name(PasswordInput)
    assert names["size"].default == "'md'"
    assert names["revealable"].default == "False"


def test_a_long_literal_is_cut_short() -> None:
    assert "more" in _by_name(TextInput)["autocomplete"].signature


def test_what_a_base_form_control_adds_is_listed() -> None:
    names = _by_name(TextInput)
    assert {"name", "label", "error", "hint"} <= names.keys()


def test_the_docstring_s_first_paragraph_is_the_description() -> None:
    assert _by_name(Button)["pill"].doc.startswith("Round the ends fully")


def test_a_literal_alias_in_a_union_is_spelled_out() -> None:
    signature = _by_name(Empty)["title"].signature
    assert "'h1' | 'h2'" in signature
    assert signature.endswith("| None = None)")
