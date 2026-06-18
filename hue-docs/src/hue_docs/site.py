"""Base-URL handling for deploys served from a subpath.

Set ``HUE_DOCS_BASE_URL`` (e.g. ``/hue``) when the site is served from a
subpath — most notably a GitHub Pages *project* site at
``https://<user>.github.io/<repo>/``. It is prefixed onto the root-relative
URLs emitted into the HTML (asset links, navigation, internal links). The
``dist/`` file layout stays flat regardless, so the same build deploys to a
domain root (Vercel, custom domain) by leaving the variable unset.
"""

from __future__ import annotations

import os

BASE = os.environ.get("HUE_DOCS_BASE_URL", "").strip().rstrip("/")


def url(path: str) -> str:
    """Prefix a root-relative path (e.g. ``/styles/app.css``) with the base URL.

    Absolute and protocol-relative URLs (``https://…``, ``//cdn/…``) and
    non-root paths are returned unchanged.
    """
    if not BASE:
        return path
    if not path.startswith("/") or path.startswith("//"):
        return path
    if path == "/":
        return f"{BASE}/"
    return f"{BASE}{path}"
