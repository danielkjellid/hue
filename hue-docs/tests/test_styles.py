"""
Every class a component renders must exist in the stylesheet hue ships.

This guards the quiet failure mode of a utility-CSS component library: a
mistyped class, or one whose design token was never defined, renders as nothing
at all - no error, no warning, just an unstyled component. Nothing else in
either suite would notice, because the markup stays perfectly valid.

It lives here rather than in hue-python because this is where axis discovery
is: checking only example() would miss every non-default variant, which is
most of the class names in the system. The assertion is against hue's own
built stylesheet, not the docs one, since that is what a consumer gets.

A failure usually means a typo, or a stylesheet that was not rebuilt after the
classes changed (make build-css in hue-python).
"""

from __future__ import annotations

import html as html_lib
import re

import pytest
from hue.assets import css_built_path

from hue_docs.discovery import discover
from hue_docs.registry import auto_showcases, example_instance
from hue_docs.render import render_html_sync
from hue_docs.showcase import curated_showcases

_CSS = css_built_path().read_text()


def _css_escape(token: str) -> str:
    """A class name as Tailwind writes it into a selector."""
    return "".join(c if (c.isalnum() or c in "-_") else "\\" + c for c in token)


def _is_defined(token: str) -> bool:
    return (
        re.search(r"\." + re.escape(_css_escape(token)) + r"(?![\w-])", _CSS)
        is not None
    )


def _classes_in_source(code: str | None) -> set[str]:
    """Class names written by hand in a curated showcase snippet."""
    return {
        token
        for literal in re.findall(r'class_\(\s*"([^"]*)"', code or "")
        for token in literal.split()
    }


def _classes(html: str) -> set[str]:
    return {
        token
        for attr in re.findall(r'class="([^"]*)"', html)
        for token in html_lib.unescape(attr).split()
    }


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_rendered_class_exists_in_the_stylesheet(doc):
    # Every showcase variant, so non-default variants and sizes are covered
    # too - they are where most of the class names live.
    used = _classes(render_html_sync(example_instance(doc)))
    authored: set[str] = set()
    for showcase in curated_showcases(doc) + auto_showcases(doc):
        for showcase_variant in showcase.variants:
            used |= _classes(render_html_sync(showcase_variant.build()))
            # A curated snippet may call .class_() with a docs-only utility.
            # Those are the docs' own stylesheet's problem, not hue's.
            authored |= _classes_in_source(showcase_variant.code)

    undefined = sorted(token for token in used - authored if not _is_defined(token))

    assert not undefined, (
        f"{doc.name} renders classes that are not in hue's tailwind.css: "
        f"{', '.join(undefined)}. Either they are mistyped, or the stylesheet "
        f"needs rebuilding (make build-css in hue-python)."
    )
