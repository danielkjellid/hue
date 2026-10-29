"""
Base-URL handling for a site served from a subpath.

Set HUE_DOCS_BASE_URL (such as /hue) when the site is served under a path
rather than at a domain's root. It is prefixed onto the root-relative URLs
in the HTML: asset links, navigation and internal links. The dist-v2 layout
stays flat either way, so the same build serves from a root by leaving the
variable unset, as the Cloudflare deploy does.
"""

from __future__ import annotations

import os

BASE = os.environ.get("HUE_DOCS_BASE_URL", "").strip().rstrip("/")


def url(path: str) -> str:
    """
    Prefix a root-relative path, such as /styles/app.css, with the base URL.

    Absolute and protocol-relative URLs (https://… and //cdn/…) and relative
    paths are returned unchanged.
    """
    is_root_relative = path.startswith("/") and not path.startswith("//")
    return f"{BASE}{path}" if is_root_relative else path
