"""
The code beside a preview is the code that rendered it.
"""

from __future__ import annotations

import ast

import pytest
from hue.ui import Button

from hue_docs_v2.layout.panel import panel_code
from hue_docs_v2.pages import COMPONENTS
from hue_docs_v2.snippets import SnippetError, imports, snippet

PANELS = [(page, panel) for page in COMPONENTS for panel in page.panels]


@pytest.mark.parametrize(
    "page,panel", PANELS, ids=[f"{page.slug}:{panel.slug}" for page, panel in PANELS]
)
def test_a_panel_shows_code_that_runs(page, panel) -> None:
    # Every example is one return, and the block it adds up to parses.
    ast.parse(panel_code(panel))


def _one_line():
    return Button().variant("primary")


def _wrapped():
    # Long enough that the formatter keeps it wrapped.
    return (
        Button()
        .variant("primary")
        .content("Save the changes to this invoice and send it out")
    )


def _two_statements():
    label = "Save"
    return Button().content(label)


def test_a_one_line_return_is_shown_as_written() -> None:
    assert snippet(_one_line) == 'Button().variant("primary")'


def test_a_wrapped_chain_keeps_its_parentheses_and_loses_the_indent() -> None:
    assert snippet(_wrapped).splitlines() == [
        "(",
        "    Button()",
        '    .variant("primary")',
        '    .content("Save the changes to this invoice and send it out")',
        ")",
    ]


def test_anything_but_a_single_return_is_refused() -> None:
    with pytest.raises(SnippetError):
        snippet(_two_statements)


def test_imports_name_what_the_code_uses() -> None:
    assert imports('Stack().content(Button(), html.p("x"))') == (
        "from hue import html\nfrom hue.ui import Button, Stack"
    )


def test_an_icon_is_bound_by_the_reader() -> None:
    lines = imports('Button().content(Icon("plus"))').splitlines()
    assert "from hue.ui import Button, create_icon_base" in lines
    assert any(line.startswith("Icon = create_icon_base(") for line in lines)
