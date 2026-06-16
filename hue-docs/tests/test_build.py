import pytest

from hue_docs import content
from hue_docs.build import build_nav
from hue_docs.categories import CATEGORY_ORDER, DEFAULT_CATEGORY
from hue_docs.discovery import discover
from hue_docs.layout.page import build_page
from hue_docs.layout.playground import playground as build_playground
from hue_docs.layout.showcase import component_main
from hue_docs.registry import auto_showcases, load_examples
from hue_docs.render import render_html_sync


def test_nav_includes_prose_groups_and_component_categories():
    docs = discover()
    nav = build_nav(content.PAGES, docs)
    titles = [group.title for group in nav]

    assert "Get started" in titles
    # Related components are clustered into subsections, not one flat list.
    assert "Inputs" in titles

    category_titles = set(CATEGORY_ORDER) | {DEFAULT_CATEGORY}
    component_items = sum(
        len(group.items) for group in nav if group.title in category_titles
    )
    assert component_items == len(docs)


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
    examples = load_examples()
    example = examples.get(doc.name)
    showcases = example.showcases if example else auto_showcases(doc)

    nav = build_nav(content.PAGES, discover())
    html = render_html_sync(
        build_page(
            title=doc.name,
            nav=nav,
            active_href=f"/components/{doc.slug}/",
            main=component_main(doc, showcases),
        )
    )

    assert html.startswith("<!DOCTYPE html>")
    assert doc.name in html
    # Every showcased variant must have rendered without falling back to error.
    assert "Could not render:" not in html


def test_playgrounds_render_without_error():
    docs = {doc.name: doc for doc in discover()}
    for name, example in load_examples().items():
        if example.playground is None:
            continue
        component = build_playground(docs[name], example.playground)
        assert component is not None, f"{name} playground produced no controls"
        html = render_html_sync(component)
        assert "Could not render:" not in html, f"{name} playground had a render error"


def test_every_example_variant_builds_and_renders():
    for name, example in load_examples().items():
        for showcase in example.showcases:
            for variant in showcase.variants:
                html = render_html_sync(variant.build())
                assert html, f"{name}/{showcase.title}/{variant.label} rendered empty"
