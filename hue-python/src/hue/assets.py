import hashlib
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path


def _static_path() -> Path:
    resource = files("hue").joinpath("static")
    return Path(str(resource))


def css_source_path() -> Path:
    """
    Path to tailwind.input.css, the theme source file.

    An escape hatch for users who need deep customisation, such as importing
    hue's theme variables into their own Tailwind build.
    """
    return _static_path() / "styles" / "tailwind.input.css"


def css_built_path() -> Path:
    """
    Path to the pre-built tailwind.css file.
    """
    return _static_path() / "styles" / "tailwind.css"


def js_bundle_path() -> Path:
    """
    Path to the pre-built Alpine.js bundle.
    """
    return _static_path() / "js" / "alpine-bundle.js"


def chart_bundle_path() -> Path:
    """
    Path to the chart library, built apart from the Alpine bundle, which
    fetches it by this file name from its own directory.
    """
    return _static_path() / "js" / "chart-bundle.js"


def icons_path() -> Path:
    """
    Path to the small icon set hue ships for its own components.
    """
    return _static_path() / "icons"


def read_css() -> str:
    """
    Read the built CSS. Used by framework middleware.

    The stylesheet is generated rather than committed, so a fresh checkout has
    to build it once.
    """
    path = css_built_path()
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"hue's stylesheet has not been built yet ({path}). It is generated "
            f"rather than committed: run `make build-css` in hue-python, or "
            f"`make build` to produce the JS bundle too."
        ) from None


def read_js() -> str:
    """
    Read the JS bundle. Used by framework middleware.
    """
    return js_bundle_path().read_text(encoding="utf-8")


def read_chart_js() -> str:
    """
    Read the chart library. Used by framework middleware.
    """
    return chart_bundle_path().read_text(encoding="utf-8")


# Where an integration serves hue's own assets, with no static files step.
# The chart bundle sits beside the Alpine bundle, which fetches it by name
# from its own directory.
ASSETS_PREFIX = "/__hue__/"
CSS_URL = f"{ASSETS_PREFIX}styles.css"
JS_URL = f"{ASSETS_PREFIX}js/alpine.js"
CHART_JS_URL = f"{ASSETS_PREFIX}js/{chart_bundle_path().name}"

# URL -> (content reader, content type)
ASSET_ROUTES: dict[str, tuple[Callable[[], str], str]] = {
    CSS_URL: (read_css, "text/css; charset=utf-8"),
    JS_URL: (read_js, "text/javascript; charset=utf-8"),
    CHART_JS_URL: (read_chart_js, "text/javascript; charset=utf-8"),
}

# URL -> (encoded content, content hash)
_served: dict[str, tuple[bytes, str]] = {}


def served_asset(url: str, *, reload: bool = False) -> tuple[bytes, str]:
    """
    An asset's content and the hash of it, read from the package on first use.

    reload reads it again, for a development server: the bundle is rebuilt
    while it runs, and a reloader restarts the server for Python only.
    """
    if url not in _served or reload:
        reader, _ = ASSET_ROUTES[url]
        content = reader().encode("utf-8")
        digest = hashlib.md5(content, usedforsecurity=False).hexdigest()
        _served[url] = (content, digest)
    return _served[url]


def versioned_url(url: str, *, reload: bool = False) -> str:
    """
    An asset's URL with the hash of its content in it, which is the URL a page
    links. A change to the asset is a new URL, so no browser holds on to the
    old one after a deploy.
    """
    return f"{url}?v={served_asset(url, reload=reload)[1]}"


def cache_control(digest: str, requested: str | None) -> str:
    """
    The Cache-Control for an asset whose content hashes to digest, asked for
    with requested as its ?v=.

    Cached for good when the URL names this content, since it can never
    change. Anything else, such as a link written without the hash, asks again
    each time and gets a 304 while the ETag still matches.
    """
    if requested == digest:
        return "public, max-age=31536000, immutable"
    return "public, no-cache"
