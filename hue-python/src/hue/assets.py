from importlib.resources import files
from pathlib import Path


def _static_path() -> Path:
    """Get the path to hue's static directory."""
    resource = files("hue").joinpath("static")
    return Path(str(resource))


def css_source_path() -> Path:
    """Path to tailwind.input.css (the theme source file).

    Exposed as an escape hatch for users who need deep customization,
    e.g. importing Hue's theme variables into their own Tailwind build.
    """
    return _static_path() / "styles" / "tailwind.input.css"


def css_built_path() -> Path:
    """Path to the pre-built tailwind.css file."""
    return _static_path() / "styles" / "tailwind.css"


def js_bundle_path() -> Path:
    """Path to the pre-built Alpine.js bundle."""
    return _static_path() / "js" / "alpine-bundle.js"


def read_css() -> str:
    """Read the pre-built CSS content. Used by framework middleware."""
    return css_built_path().read_text()


def read_js() -> str:
    """Read the JS bundle content. Used by framework middleware."""
    return js_bundle_path().read_text()
