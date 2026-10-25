"""
The whole site, frozen to files and indexed for search.
"""

from __future__ import annotations

import json
from pathlib import Path

from hue_docs_v2.app import frame_paths, page_paths


def test_every_page_and_frame_is_written(frozen: Path) -> None:
    for path in page_paths() + frame_paths():
        assert (frozen / path.strip("/") / "index.html").exists(), path


def test_the_search_index_holds_every_page(frozen: Path) -> None:
    entry = json.loads((frozen / "pagefind" / "pagefind-entry.json").read_text())
    assert sum(
        language["page_count"] for language in entry["languages"].values()
    ) == len(page_paths())


def test_redirects_are_written_for_the_host(frozen: Path) -> None:
    assert "/toasts/ /components/toast/ 301" in (frozen / "_redirects").read_text()


def test_the_scripts_the_pages_load_are_there(frozen: Path) -> None:
    for name in ("js/alpine-bundle.js", "static/docs.js", "pagefind/pagefind.js"):
        assert (frozen / name).exists(), name
