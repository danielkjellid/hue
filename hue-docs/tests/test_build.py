"""
The whole site, frozen to files and indexed for search.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hue_docs.app import REDIRECTS, frame_paths, page_paths


def test_every_page_and_frame_is_written(frozen: Path) -> None:
    for path in page_paths() + frame_paths():
        assert (frozen / path.strip("/") / "index.html").exists(), path


def test_the_search_index_holds_every_page(frozen: Path) -> None:
    entry = json.loads((frozen / "pagefind" / "pagefind-entry.json").read_text())
    assert sum(
        language["page_count"] for language in entry["languages"].values()
    ) == len(page_paths())


@pytest.mark.parametrize("old,new", REDIRECTS.items())
def test_redirects_are_written_for_the_host(frozen: Path, old: str, new: str) -> None:
    assert f"{old} {new} 301" in (frozen / "_redirects").read_text()


def test_the_scripts_the_pages_load_are_there(frozen: Path) -> None:
    for name in ("js/alpine-bundle.js", "static/docs.js", "pagefind/pagefind.js"):
        assert (frozen / name).exists(), name


def test_the_favicon_redirect_is_at_the_domain_s_root(frozen: Path) -> None:
    # Browsers ask for /favicon.ico whatever path the site is served under.
    lines = (frozen / "_redirects").read_text().splitlines()
    assert any(line.startswith("/favicon.ico ") for line in lines)
