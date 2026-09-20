"""A styled, copyable code block. Uses the bundled Alpine for copy — no JS deps."""

from __future__ import annotations

from hue import html
from hue.js import unsafe
from hue.types.core import ComponentType

from hue_docs.layout.highlight import highlight_code


def code_block(source: str, *, language: str = "python") -> ComponentType:
    return (
        html.div()
        .class_("group relative")
        .x_data("{ copied: false }")
        .content(
            html.button("Copy")
            .aria_label("Copy code to clipboard")
            .class_(
                "absolute right-2 top-2 rounded-md border border-surface-200 "
                "bg-background px-2 py-1 text-xs text-surface-600 opacity-0 "
                "transition-opacity hover:text-surface-900 group-hover:opacity-100 "
                "focus-visible:opacity-100"
            )
            .x_on(
                "click",
                unsafe(
                    "navigator.clipboard.writeText($refs.code.textContent);"
                    " copied = true; setTimeout(() => copied = false, 1200)"
                ),
            )
            .x_text(unsafe("copied ? 'Copied' : 'Copy'")),
            html.pre(
                # The copy button reads the highlighted element's own text,
                # which is the source with the markup stripped back off. A
                # second, hidden copy of it would be the same page weight
                # twice - and a snippet that mentions an id would put that id
                # on the page as text, where anything reading the document
                # for real ones finds it.
                html.code(highlight_code(source, language)).x_ref("code"),
            ).class_(
                "highlight overflow-x-auto rounded-lg border border-surface-200 "
                "bg-surface-50 p-4 text-sm leading-6 "
                "font-mono dark:border-surface-100 dark:bg-surface-900"
            ),
        )
    )
