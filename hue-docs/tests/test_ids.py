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


def _prose_html(page: content.ProsePage) -> str:
    return render_html_sync(
        build_page(
            title=page.title,
            nav=build_nav(content.PAGES, discover()),
            active_href=f"/{page.slug}",
            main=page.build(),
        )
    )


def _live_ids(html: str) -> list[str]:
    """
    The ids of the page's own controls.

    A code sample is text about markup rather than markup, and the block
    that holds one keeps a raw copy of the source for the copy button -
    so its ids are neither live nor the page's to keep unique.
    """
    return re.findall(r'\sid="([^"]+)"', re.sub(r"<pre[\s\S]*?</pre>", "", html))


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
    ids = _live_ids(_page_html(doc))
    repeated = {name: n for name, n in collections.Counter(ids).items() if n > 1}

    assert not repeated, (
        f"the {doc.name} page repeats ids {sorted(repeated)}. Two controls on "
        f"one page cannot share a name: a label points at the first match in "
        f"the document, not the nearest one."
    )


@pytest.mark.parametrize("page", content.PAGES, ids=lambda page: page.title)
def test_no_id_appears_twice_in_the_prose_pages(page: content.ProsePage) -> None:
    """
    The same rule, for the pages that are written rather than discovered.

    A guide that puts two of the same thing on one page to show two
    states of it has two of every id inside them, and a label in the
    second points at a control in the first.
    """
    ids = _live_ids(_prose_html(page))
    repeated = {name: n for name, n in collections.Counter(ids).items() if n > 1}

    assert not repeated, (
        f"the {page.title} page repeats ids {sorted(repeated)}. Two controls "
        f"on one page cannot share a name: a label points at the first match "
        f"in the document, not the nearest one."
    )


@pytest.mark.parametrize("doc", discover(), ids=lambda doc: doc.name)
def test_only_one_playground_combination_is_ever_live(doc: ComponentDoc) -> None:
    """
    Hidden is not the same as absent.

    Every combination used to be rendered and then merely hidden, so all of
    them were live at once: twelve pre-rendered dialogs each said open: true,
    fired a focus trap at load and left the page unable to scroll. A template
    is inert until Alpine clones it, so the page holds exactly the one that is
    selected.
    """
    html = _page_html(doc)
    templates = len(re.findall(r"<template x-if=", html))
    shown = len(re.findall(r'x-show="sel\.', html))

    assert shown == 0, (
        f"the {doc.name} playground renders {shown} combinations live and only "
        f"hides them. They have to be templates, or everything a combination "
        f"does on init happens for all of them at once."
    )
    if templates:
        assert templates > 1
