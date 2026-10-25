"""
Every page and every frame renders, every example in it, and no id repeats.
"""

from __future__ import annotations

import collections
import inspect
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import hue
import hue_fastapi
import pytest
from fastapi.testclient import TestClient
from hue import ui
from hue.ui.base import ChainableComponent

import hue_docs_v2
from hue_docs_v2.app import REDIRECTS, demo_app, frame_paths, page_paths
from hue_docs_v2.pages import COMPONENTS
from hue_docs_v2.render import COULD_NOT_RENDER


def _live_ids(html: str) -> list[str]:
    # A code sample is text about markup, so its ids are not the page's.
    return re.findall(r'\sid="([^"]+)"', re.sub(r"<pre[\s\S]*?</pre>", "", html))


@pytest.mark.parametrize("path", page_paths() + frame_paths())
def test_renders(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert COULD_NOT_RENDER not in response.text


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
    # Pages are files the freeze wrote, never rendered by the Worker.
    assert worker.get("/components/button/").status_code == 404


# Paths the build writes beside the pages, which the dev app serves from disk.
_ASSET_DIRS = ("/static/", "/styles/", "/js/", "/pagefind/", "/__hue__/")


@pytest.mark.parametrize("path", page_paths())
def test_every_internal_link_lands_somewhere(client: TestClient, path: str) -> None:
    hrefs = re.findall(r'\shref="(/[^"#?]*)', client.get(path).text)
    known = set(page_paths()) | set(REDIRECTS)
    dead = sorted(
        {
            href
            for href in hrefs
            if href not in known
            and not href.startswith(_ASSET_DIRS)
            and not href.startswith("/demos/")
        }
    )
    assert not dead, f"{path} links to pages that do not exist: {dead}"


def test_the_worker_imports_from_only_what_it_bundles(tmp_path) -> None:
    """
    The Worker bundles Python files and the SVGs a rule adds, nothing else, so
    the demo app must import and answer from such a copy of the package.
    """
    # The three packages make worker-v2 copies in, each read from its source.
    for package in (hue, hue_fastapi, hue_docs_v2):
        source = Path(package.__file__).parent
        for path in source.rglob("*"):
            if path.suffix in {".py", ".svg"} and "node_modules" not in path.parts:
                target = tmp_path / source.name / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(path, target)
    script = (
        "from fastapi.testclient import TestClient\n"
        "from hue_docs_v2.app import demo_app\n"
        "r = TestClient(demo_app()).post("
        "'/demos/toast/send/', headers={'X-Alpine-Request': 'true'})\n"
        "assert r.status_code == 200, r.status_code\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_every_documented_component_has_a_page() -> None:
    documented = {
        name
        for name in ui.__all__
        if isinstance(cls := getattr(ui, name), type)
        and issubclass(cls, ChainableComponent)
        and not inspect.isabstract(cls)
        and cls is not ChainableComponent
        and cls.category is not None
    }
    have = {page.component.__name__ for page in COMPONENTS}
    assert documented <= have, f"no page for {sorted(documented - have)}"
