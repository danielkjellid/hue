from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hue.formats import Formats
from hue.shortcuts import ShortcutRegistry
from starlette.applications import Starlette

from hue_fastapi.assets import add_asset_routes

if TYPE_CHECKING:
    from hue_fastapi.csrf import CsrfConfig


class HueNotConfiguredError(RuntimeError):
    """
    Raised when a hue view renders on an app that was never configured.
    """


def _default_title(title: str) -> str:
    return f"{title} - Hue"


@dataclass(frozen=True, slots=True)
class HueConfig:
    """
    Everything hue needs to know about the application it is rendering into.

    Held on app.state and read when a page renders, so one process can serve
    several apps with different settings and a test can build a throwaway app
    per case.
    """

    # None turns hue's CSRF checking off, for apps that bring their own.
    csrf: CsrfConfig | None
    # None means hue's own assets, linked by a URL that names their content.
    css_url: str | None = None
    js_url: str | None = None
    extra_css_urls: tuple[str, ...] = ()
    html_title_factory: Callable[[str], str] = _default_title
    formats: Formats = field(default_factory=Formats)
    shortcuts: type[ShortcutRegistry] | None = None


def configure_hue(
    app: Starlette,
    *,
    csrf: CsrfConfig | None,
    css_url: str | None = None,
    js_url: str | None = None,
    extra_css_urls: Sequence[str] = (),
    html_title_factory: Callable[[str], str] = _default_title,
    formats: Formats | None = None,
    shortcuts: type[ShortcutRegistry] | None = None,
) -> HueConfig:
    """
    Attach hue to a FastAPI application and serve its assets.

    Pass css_url when the application compiles its own stylesheet: hue's built
    CSS holds only the classes hue itself uses, so an app writing Tailwind
    classes of its own needs a build that sees both. shortcuts is the app's
    ShortcutRegistry, which every page binds.

    csrf is required rather than defaulted, so turning protection off is a
    decision someone made on purpose.
    """
    config = HueConfig(
        csrf=csrf,
        css_url=css_url,
        js_url=js_url,
        extra_css_urls=tuple(extra_css_urls),
        html_title_factory=html_title_factory,
        formats=formats or Formats(),
        shortcuts=shortcuts,
    )
    app.state.hue = config
    add_asset_routes(app)
    return config


def get_config(app: Starlette) -> HueConfig:
    config = getattr(app.state, "hue", None)
    if config is None:
        raise HueNotConfiguredError(
            "This app has no hue configuration. Call "
            "hue_fastapi.configure_hue(app, csrf=...) during startup."
        )
    return config
