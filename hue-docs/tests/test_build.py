import pytest

from hue_docs import content
from hue_docs.build import build_nav
from hue_docs.categories import CATEGORY_ORDER, DEFAULT_CATEGORY
from hue_docs.discovery import discover
from hue_docs.layout.page import build_page
from hue_docs.layout.playground import playground as build_playground
from hue_docs.layout.showcase import component_main
from hue_docs.registry import auto_showcases, example_code, example_instance
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
    nav = build_nav(content.PAGES, discover())
    html = render_html_sync(
        build_page(
            title=doc.name,
            nav=nav,
            active_href=f"/components/{doc.slug}/",
            main=component_main(doc, auto_showcases(doc), build_playground(doc)),
        )
    )

    assert html.startswith("<!DOCTYPE html>")
    assert doc.name in html
    # Nothing on the page should have fallen back to a render error.
    assert "Could not render:" not in html


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_component_exposes_a_renderable_example(doc):
    # The whole auto-discovery story depends on each component providing a
    # representative, renderable example() instance.
    html = render_html_sync(example_instance(doc))
    assert html, f"{doc.name}.example() rendered empty"
    # And its source is recoverable as a usage snippet starting with the name.
    code = example_code(doc)
    assert code is None or code.startswith(f"{doc.name}(")


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_every_component_playground_renders(doc):
    component = build_playground(doc)
    if component is None:  # components with no enum/bool axes (e.g. Icon)
        return
    html = render_html_sync(component)
    assert "Could not render:" not in html, f"{doc.name} playground had a render error"


def test_every_showcase_variant_builds_and_renders():
    for doc in discover():
        for showcase in auto_showcases(doc):
            for variant in showcase.variants:
                html = render_html_sync(variant.build())
                assert html, f"{doc.name}/{showcase.title}/{variant.label} was empty"
