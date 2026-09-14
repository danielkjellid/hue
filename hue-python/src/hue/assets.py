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
