"""
Write the site to static files: every page and frame as the app serves it, the
scripts the pages load, and the search index over the pages.

The stylesheet is built by the Makefile into the same directory first, since
the Tailwind CLI is a separate step.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from hue.assets import chart_bundle_path, js_bundle_path
from pagefind.index import IndexConfig, PagefindIndex

from hue_docs_v2.app import REDIRECTS, STATIC, create_app, frame_paths, page_paths
from hue_docs_v2.highlight import highlight
from hue_docs_v2.render import COULD_NOT_RENDER
from hue_docs_v2.site import url

DIST = Path(__file__).resolve().parents[2] / "dist-v2"


def _fetch(client: TestClient, path: str) -> str:
    response = client.get(path)
    if response.status_code != 200:
        raise RuntimeError(f"{path} answered {response.status_code}")
    if COULD_NOT_RENDER in response.text:
        raise RuntimeError(f"An example on {path} failed to render.")
    return response.text


def _write(out: Path, path: str, html: str) -> None:
    target = out / path.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


async def _index(out: Path, pages: dict[str, str]) -> None:
    config = IndexConfig(output_path=str(out / "pagefind"))
    async with PagefindIndex(config=config) as index:
        for path, html in pages.items():
            await index.add_html_file(content=html, url=url(path))


def freeze(out: Path = DIST) -> None:
    client = TestClient(create_app())
    paths = page_paths() + frame_paths()

    # One pass to find every code block that is not highlighted yet, which
    # are then highlighted in a single run of Shiki.
    with highlight.record():
        for path in paths:
            client.get(path)

    pages = {path: _fetch(client, path) for path in page_paths()}
    for path, html in pages.items():
        _write(out, path, html)
    for path in frame_paths():
        _write(out, path, _fetch(client, path))

    (out / "js").mkdir(parents=True, exist_ok=True)
    for bundle in (js_bundle_path(), chart_bundle_path()):
        shutil.copy(bundle, out / "js" / bundle.name)
    shutil.copytree(STATIC, out / "static", dirs_exist_ok=True)
    # Cloudflare's static assets read redirects from this file.
    (out / "_redirects").write_text(
        "".join(f"{url(old)} {url(new)} 301\n" for old, new in REDIRECTS.items())
    )

    shutil.rmtree(out / "pagefind", ignore_errors=True)
    asyncio.run(_index(out, pages))
    print(f"Wrote {len(pages)} pages and {len(paths) - len(pages)} frames to {out}")


if __name__ == "__main__":
    freeze(Path(sys.argv[1]) if len(sys.argv) > 1 else DIST)
