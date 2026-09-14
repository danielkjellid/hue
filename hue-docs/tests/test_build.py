from pathlib import Path

import pytest

from hue_docs import content, showcase
from hue_docs.build import build_nav
from hue_docs.categories import ordered_categories
from hue_docs.discovery import discover
from hue_docs.layout.highlight import highlight_code
from hue_docs.layout.page import build_page
from hue_docs.layout.playground import playground as build_playground
from hue_docs.layout.showcase import component_main
from hue_docs.models import ProsePage
from hue_docs.registry import auto_showcases, example_instance
from hue_docs.render import render_html_sync
from hue_docs.showcase import curated_showcases


def test_nav_includes_prose_groups_and_component_categories():
    docs = discover()
    nav = build_nav(content.PAGES, docs)
    titles = [group.title for group in nav]

    assert "Get started" in titles
    # Related components are clustered into subsections, not one flat list.
    assert "Inputs" in titles

    categories = set(ordered_categories(docs))
    component_items = sum(
        len(group.items) for group in nav if group.title in categories
    )
    assert component_items == len(docs)


def test_nav_rejects_unknown_prose_groups():
    page = ProsePage(
        slug="x", title="X", nav_label="X", group="Typo", order=1, build=lambda: ""
    )
    with pytest.raises(ValueError, match="Typo"):
        build_nav([page], [])


def test_component_category_comes_from_the_component():
    docs = {doc.name: doc for doc in discover()}
    # Categories are declared on the component class, not a docs-side map.
    assert docs["Button"].category == "Actions"
    assert docs["TextInput"].category == "Inputs"
    assert docs["Stack"].category == "Layout"


def test_unknown_code_language_is_rejected():
    with pytest.raises(ValueError, match="Unknown code block language"):
        highlight_code("<svg/>", "htlm")


@pytest.mark.parametrize("page", content.PAGES, ids=lambda p: p.slug or "home")
def test_prose_pages_render_to_a_document(page):
    nav = build_nav(content.PAGES, discover())
    html = render_html_sync(
        build_page(
            title=page.title,
            nav=nav,
            active_href=page.href,
            main=page.build(),
        )
    )

    assert html.startswith("<!DOCTYPE html>")
    assert f"{page.title} · Hue" in html
    assert "/styles/tailwind.css" in html


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_component_page_renders(doc):
    # Exercises the header, curated and auto showcases, and the playground.
    nav = build_nav(content.PAGES, discover())
    showcases = curated_showcases(doc) + auto_showcases(doc)
    html = render_html_sync(
        build_page(
            title=doc.name,
            nav=nav,
            active_href=doc.href,
            main=component_main(doc, showcases, build_playground(doc)),
        )
    )

    assert html.startswith("<!DOCTYPE html>")
    assert doc.name in html
    assert "Could not render:" not in html


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_component_exposes_a_renderable_example(doc):
    # The whole auto-discovery story depends on each component providing a
    # representative, renderable example() instance.
    assert render_html_sync(example_instance(doc)), f"{doc.name}.example() was empty"


def test_every_curated_showcase_module_matches_a_component():
    names = {doc.name for doc in discover()}
    modules = {
        path.stem
        for path in Path(showcase.__file__).parent.glob("*.py")
        if path.stem != "__init__"
    }
    assert modules <= names, f"orphan showcase modules: {modules - names}"
