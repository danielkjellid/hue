"""
Every class a component renders must exist in the stylesheet hue ships.

This guards the quiet failure mode of a utility-CSS component library: a
mistyped class, or one whose design token was never defined, renders as nothing
at all - no error, no warning, just an unstyled component. Nothing else in
either suite would notice, because the markup stays perfectly valid.

The stylesheet is built for the test session rather than read from disk, so
this asserts against what the current source produces.

It lives here rather than in hue-python because this is where axis discovery
is: checking only example() would miss every non-default variant, which is
most of the class names in the system. The assertion is against hue's own
built stylesheet, not the docs one, since that is what a consumer gets.

A failure means a class name that no rule matches - almost always a typo, or a
design token that was never defined. It says nothing about how Tailwind found
the class: that is Tailwind's own business, and tested by Tailwind.
"""

from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup
from hue.assets import css_source_path

from hue_docs.discovery import discover
from hue_docs.registry import auto_showcases, example_instance
from hue_docs.render import render_html_sync
from hue_docs.showcase import curated_showcases

SOURCE = css_source_path().parent


def _css_escape(token: str) -> str:
    """A class name as Tailwind writes it into a selector."""
    return "".join(c if (c.isalnum() or c in "-_") else "\\" + c for c in token)


def _is_defined(token: str, css: str) -> bool:
    pattern = r"\." + re.escape(_css_escape(token)) + r"(?![\w-])"
    return re.search(pattern, css) is not None


def _classes(html: str) -> set[str]:
    """
    Every class name the rendered markup actually puts on an element.

    Parsed rather than pattern-matched, so Alpine's :class - an expression,
    not a class list - is simply a different attribute and never has to be
    told apart from this one.
    """
    soup = BeautifulSoup(html, "html.parser")
    return {token for el in soup.select("[class]") for token in el["class"]}


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_rendered_class_exists_in_the_stylesheet(doc, built_css):
    # Every showcase variant, so non-default variants and sizes are covered
    # too - they are where most of the class names live.
    used = _classes(render_html_sync(example_instance(doc)))
    for showcase in curated_showcases(doc) + auto_showcases(doc):
        for showcase_variant in showcase.variants:
            used |= _classes(render_html_sync(showcase_variant.build()))

    undefined = sorted(token for token in used if not _is_defined(token, built_css))

    assert not undefined, (
        f"{doc.name} renders classes that are not in hue's tailwind.css: "
        f"{', '.join(undefined)}. Either they are mistyped, or the stylesheet "
        f"needs rebuilding (make build-css in hue-python)."
    )


def test_no_token_is_referenced_without_being_defined() -> None:
    """
    A var() pointing at nothing renders nothing, and says nothing about it.

    The declaration is simply dropped: a square corner where a round one was
    meant, a transparent fill, a missing shadow. Nothing in either suite would
    notice, because the class is present and the stylesheet is valid - which
    is how --radius-full went missing from the slider's track.
    """
    source = (SOURCE / "tailwind.input.css").read_text()
    defined = set(re.findall(r"^\s*(--[\w-]+)\s*:", source, re.M))
    used = set(re.findall(r"var\((--[\w-]+)", source))
    # Tailwind supplies its own --tw-* internals.
    missing = sorted(t for t in used - defined if not t.startswith("--tw-"))

    assert not missing, (
        f"hue's stylesheet reads {', '.join(missing)} without defining them. "
        f"A var() with nothing behind it drops the whole declaration."
    )
