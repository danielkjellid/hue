"""
A highlighted code block with a copy button.
"""

from __future__ import annotations

from htmy import SafeStr
from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import Button

from hue_docs_v2.highlight import highlight
from hue_docs_v2.icons import Icon

_COPY = (
    "navigator.clipboard.writeText($refs.code.textContent.trim());"
    " copied = true; setTimeout(() => copied = false, 1500)"
)


def copy_button(label: str = "Copy code") -> ComponentType:
    return (
        Button()
        .variant("ghost")
        .size("xs")
        .icon_only(label)
        .content(
            html.span(Icon("copy")).x_show(unsafe("!copied")),
            html.span(Icon("check")).x_show(unsafe("copied")).x_cloak(),
        )
        .x_on("click", unsafe(_COPY))
    )


def code_block(source: str, *, language: str = "python") -> ComponentType:
    """
    The copy button reads the highlighted element's own text, which is the
    source with the markup stripped back off, so the page carries it once.
    """
    return (
        html.div(
            html.div(copy_button()).class_(
                "absolute end-2 top-2 opacity-0 transition-opacity "
                "group-hover:opacity-100 group-focus-within:opacity-100"
            ),
            html.div(SafeStr(highlight(source, language))).x_ref("code"),
            # Announced by itself when a copy lands, since the icon swap says
            # nothing to a screen reader.
            html.span()
            .class_("sr-only")
            .aria_live("polite")
            .x_text(unsafe("copied ? 'Copied' : ''")),
        )
        .class_("docs-code group relative")
        .x_data("{ copied: false }")
    )
