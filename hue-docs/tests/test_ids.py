"""
No id appears twice on a component page.

A page puts every showcase variant, and every playground combination, into
one document at once - so a component that names its own id from a prop
collides with its own copies. The markup stays valid and the page looks
right; it is the behaviour that breaks, because a label points at the first
matching id in the document rather than the one beside it. Clicking a card in
the playground then toggles a checkbox nobody can see.

Rendered here rather than read out of dist/, which is generated and ignored:
on a machine that has never run the build there would be nothing to check,
and on one that has, the answer would be whatever the last build happened to
leave behind.
"""

from __future__ import annotations

import collections
import re

import pytest

from hue_docs import content
from hue_docs.build import build_nav
from hue_docs.discovery import ComponentDoc, discover
from hue_docs.layout.page import build_page
from hue_docs.layout.playground import playground as build_playground
from hue_docs.layout.showcase import component_main
from hue_docs.registry import auto_showcases
from hue_docs.render import render_html_sync
from hue_docs.showcase import curated_showcases


def _page_html(doc: ComponentDoc) -> str:
    showcases = curated_showcases(doc) + auto_showcases(doc)
    return render_html_sync(
        build_page(
            title=doc.name,
            nav=build_nav(content.PAGES, discover()),
            active_href=doc.href,
            main=component_main(doc, showcases, build_playground(doc)),
        )
    )


@pytest.mark.parametrize("doc", discover(), ids=lambda doc: doc.name)
def test_no_id_appears_twice(doc: ComponentDoc) -> None:
    ids = re.findall(r'\sid="([^"]+)"', _page_html(doc))
    repeated = {name: n for name, n in collections.Counter(ids).items() if n > 1}

    assert not repeated, (
        f"the {doc.name} page repeats ids {sorted(repeated)}. Two controls on "
        f"one page cannot share a name: a label points at the first match in "
        f"the document, not the nearest one."
    )


@pytest.mark.parametrize("doc", discover(), ids=lambda doc: doc.name)
def test_every_playground_block_can_be_put_back(doc: ComponentDoc) -> None:
    """
    A combination is rendered once and then only hidden and shown, so whatever
    the reader does to one of them sticks. For the indeterminate checkbox that
    is unrecoverable on its own: clicking it clears a DOM property nothing
    re-applies, so the state could be seen exactly once per page load.
    """
    html = _page_html(doc)
    shown = len(re.findall(r'x-show="sel\.', html))
    restored = html.count("_initial?.forEach")

    assert restored == shown, (
        f"the {doc.name} page has {shown} playground combinations but "
        f"{restored} that restore themselves when selected again."
    )
