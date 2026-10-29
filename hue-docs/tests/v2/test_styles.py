"""
Every class on a page or in a frame exists in the stylesheet the site ships.

A mistyped class, or one naming a token that was never defined, renders as
nothing at all, and no other check would notice.
"""

from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from hue_docs_v2.app import frame_paths, page_paths


def _defined(token: str, css: str) -> bool:
    escaped = "".join(c if (c.isalnum() or c in "-_") else "\\" + c for c in token)
    return re.search(r"\." + re.escape(escaped) + r"(?![\w-])", css) is not None


@pytest.mark.parametrize("path", page_paths() + frame_paths())
def test_every_class_is_defined(client: TestClient, built_css: str, path: str) -> None:
    soup = BeautifulSoup(client.get(path).text, "html.parser")
    # Shiki's markup is styled by the docs' own rules on its root class.
    for pre in soup.select("pre.shiki"):
        pre.decompose()
    tokens = {token for el in soup.find_all(class_=True) for token in el["class"]}
    missing = sorted(token for token in tokens if not _defined(token, built_css))
    assert not missing, f"{path} uses classes no rule matches: {missing}"
