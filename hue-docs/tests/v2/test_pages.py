"""
Every page and every frame renders, every example in it, and no id repeats.
"""

from __future__ import annotations

import collections
import re

import pytest
from fastapi.testclient import TestClient

from hue_docs_v2.app import REDIRECTS, demo_app, frame_paths, page_paths
from hue_docs_v2.pages import COMPONENTS


def _live_ids(html: str) -> list[str]:
    # A code sample is text about markup, so its ids are not the page's.
    return re.findall(r'\sid="([^"]+)"', re.sub(r"<pre[\s\S]*?</pre>", "", html))


@pytest.mark.parametrize("path", page_paths() + frame_paths())
def test_renders(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert "Could not render:" not in response.text


@pytest.mark.parametrize("path", page_paths() + frame_paths())
def test_no_id_appears_twice(client: TestClient, path: str) -> None:
    ids = _live_ids(client.get(path).text)
    repeated = sorted(name for name, n in collections.Counter(ids).items() if n > 1)
    assert not repeated, (
        f"{path} repeats ids {repeated}. A label points at the first match in "
        f"the document, so give each example's control a name of its own."
    )


@pytest.mark.parametrize("old,new", REDIRECTS.items())
def test_a_folded_guide_redirects(client: TestClient, old: str, new: str) -> None:
    response = client.get(old, follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == new


def test_every_panel_label_is_a_heading_the_contents_can_find(
    client: TestClient,
) -> None:
    for page in COMPONENTS:
        html = client.get(page.href).text
        for panel in page.panels:
            assert f'id="{panel.slug}"' in html


def test_a_demo_route_answers(client: TestClient) -> None:
    response = client.post("/demos/toast/send/", headers={"X-Alpine-Request": "true"})
    assert response.status_code == 200
    assert 'id="send-status"' in response.text
    # The router carries the toast behind the fragment.
    assert "Invoice sent" in response.text


def test_the_worker_runs_the_demos_and_nothing_else() -> None:
    worker = TestClient(demo_app())
    assert worker.post(
        "/demos/toast/send/", headers={"X-Alpine-Request": "true"}
    ).is_success
    # Pages are files the freeze wrote, never rendered by the Worker.
    assert worker.get("/components/button/").status_code == 404
