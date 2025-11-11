from abc import abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, ClassVar
from hue.types.core import Component, ComponentType
from hue.formatter import HueFormatter
from hue.context import HueContext, HueContextArgs
from htmy import Context, html, Renderer
import json

type X_Data = dict[str, str]


class ViewValidationMixin:
    """
    Mixin that validates required ClassVar attributes in view subclasses.

    Framework-specific base classes can use this to ensure subclasses
    have required attributes like 'title'.

    Example:
        class HueView(BaseView, ViewValidationMixin):
            title: ClassVar[str] = ""  # Provide default
            ...
    """

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        # Skip validation for BaseView itself
        if cls is BaseView:
            return

        # Skip validation for framework base classes (direct subclasses of BaseView)
        # These are meant to be subclassed by users, not used directly
        if BaseView in cls.__bases__:
            # This is a framework base class (like HueView), skip validation
            return

        # For user subclasses, check if title is defined (either directly or inherited)
        if not hasattr(cls, "title"):
            raise TypeError(
                f"{cls.__name__} must define a 'title' ClassVar. "
                "Example: title = 'My Page Title'"
            )


@dataclass
class BaseView:
    """
    A base class for all views containing
    """

    title: ClassVar[str]
    base_x_data: ClassVar[X_Data] = {"theme": "light"}
    x_data: ClassVar[X_Data] = {}

    def __init_subclass__(cls) -> None:
        """
        Base initialization for subclasses.
        Framework-specific base classes should override this to add their own validation.
        """
        super().__init_subclass__()

    @cached_property
    def css_url(self) -> str:
        raise NotImplementedError("css_url must be implemented in the subclass")

    def html_title_factory(self) -> Callable[[str], str]:
        raise NotImplementedError(
            "html_title_factory must be implemented in the subclass"
        )

    @abstractmethod
    def body(self, context: Context) -> ComponentType:
        raise NotImplementedError("body must be implemented in the subclass")

    def inject_x_data(self) -> str:
        """Convert x_data dictionary to Alpine.js x-data format.
        Example: '{ theme: "light", open: false }'
        """
        # Merge base_x_data with child's x_data, giving precedence to child's data
        combined_data = {**self.base_x_data, **self.collect_x_data()}
        return json.dumps(combined_data)

    def collect_x_data(self) -> dict:
        merged = {}
        # Walk the MRO in reverse so that the most-derived class wins
        for cls in reversed(self.__class__.__mro__):
            if hasattr(cls, "x_data"):
                value = getattr(cls, "x_data", None)
                if value is not None:
                    merged.update(value)

        return merged

    async def render[T_Request: Mapping[str, Any]](
        self, context_args: HueContextArgs[T_Request]
    ) -> str:
        page = HueContext(self, **context_args)
        renderer = Renderer()
        return await renderer.render(page)

    async def htmy(self, context: Context) -> Component:
        # Extract HueContext from the context provided by the renderer
        # This context is populated by HueContext.htmy_context()
        ctx = HueContext.from_context(context)

        return HueFormatter().in_context(
            html.DOCTYPE.html,
            html.html(
                html.head(
                    html.title(self.html_title_factory(self.title)),
                    html.meta.charset(),
                    html.meta.viewport(),
                    html.script(src="https://unpkg.com/htmx.org@2.0.2"),
                    html.script(
                        src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
                        defer=True,
                    ),
                    html.link(
                        rel="stylesheet",
                        href=self.css_url,
                        type="text/css",
                    ),
                ),
                html.body(
                    self.body(context),
                    x_data=self.inject_x_data(),
                    x_bind_data_theme="theme",
                    class_="min-h-screen bg-background relative",
                    hx_headers=json.dumps({"X-CSRFToken": ctx.csrf_token}),
                ),
            ),
        )
