from __future__ import annotations

import os
from xml.dom import minidom

from htmy import Tag, html

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent


class path(Tag):
    __slots__ = ()


class circle(Tag):
    __slots__ = ()


def _render_icon(*, icon_path: str, class_: str | None = None) -> html.svg:
    try:
        with open(icon_path, "r") as f:
            icon_file = f.read()

            icon_doc = minidom.parseString(icon_file)
            svg_element = icon_doc.getElementsByTagName("svg")[0]
            view_box = svg_element.getAttribute("viewBox")
            width = svg_element.getAttribute("width")
            height = svg_element.getAttribute("height")
            fill = svg_element.getAttribute("fill")

            paths = [
                {
                    "d": p.getAttribute("d"),
                    "stroke": p.getAttribute("stroke"),
                    "stroke-linecap": p.getAttribute("stroke-linecap"),
                    "stroke-linejoin": p.getAttribute("stroke-linejoin"),
                    "stroke-width": p.getAttribute("stroke-width"),
                    "fill": p.getAttribute("fill"),
                }
                for p in icon_doc.getElementsByTagName("path")
            ]

            circles = [
                {
                    "cx": c.getAttribute("cx"),
                    "cy": c.getAttribute("cy"),
                    "r": c.getAttribute("r"),
                    "fill": c.getAttribute("fill"),
                    "stroke": c.getAttribute("stroke"),
                    "stroke-linecap": c.getAttribute("stroke-linecap"),
                    "stroke-linejoin": c.getAttribute("stroke-linejoin"),
                    "stroke-width": c.getAttribute("stroke-width"),
                }
                for c in icon_doc.getElementsByTagName("circle")
            ]
    except FileNotFoundError as e:
        raise RuntimeError(f"Icon at {icon_path} not found") from e

    if not view_box:
        raise RuntimeError(f"No viewBox found for icon at {icon_path}")

    if not paths and not circles:  # Allow either paths or circles
        raise RuntimeError(f"No paths or circles found for icon at {icon_path}")

    svg_attrs = {}

    if fill:
        svg_attrs["fill"] = fill

    if width:
        svg_attrs["width"] = width

    if height:
        svg_attrs["height"] = height

    if class_:
        svg_attrs["class"] = class_

    return html.svg(
        *[
            path(
                **{
                    k: v
                    for k, v in {
                        "d": svg_path["d"],
                        "stroke": svg_path["stroke"],
                        "stroke_linecap": svg_path["stroke-linecap"],
                        "stroke_linejoin": svg_path["stroke-linejoin"],
                        "stroke_width": svg_path["stroke-width"],
                        "fill": svg_path["fill"],
                    }.items()
                    if v
                }
            )
            for svg_path in paths
        ],
        *[
            circle(
                **{
                    k: v
                    for k, v in {
                        "cx": svg_circle["cx"],
                        "cy": svg_circle["cy"],
                        "r": svg_circle["r"],
                        "fill": svg_circle["fill"],
                        "stroke": svg_circle["stroke"],
                        "stroke_linecap": svg_circle["stroke-linecap"],
                        "stroke_linejoin": svg_circle["stroke-linejoin"],
                        "stroke_width": svg_circle["stroke-width"],
                    }.items()
                    if v
                }
            )
            for svg_circle in circles
        ],
        viewBox=view_box,
        **svg_attrs,
    )


class Icon(ChainableComponent):
    """
    An inline SVG icon loaded from a configured icon directory.

    Reads the named ``.svg`` file from the icon set and inlines it into the
    page so it can be styled with CSS (e.g. ``.class_("size-4 text-primary")``).

    Not instantiated directly — use :func:`create_icon_base` to bind an
    ``icons_dir``, then call the returned class with an icon name.

    Example::

        Icon = create_icon_base(icons_dir="/path/to/icons")
        Icon("calendar").class_("size-4")
    """

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self._name = name

    category = "Media"

    @classmethod
    def example(cls) -> "Icon":
        """A representative instance, used by the docs site for previews."""
        icons_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "static", "icons")
        )
        return create_icon_base(icons_dir=icons_dir)("circle-info").class_("size-6")

    @property
    def icons_dir(self) -> str:
        raise NotImplementedError("Use create_icon_base() to set icons_dir")

    def _render(self, context: HueContext) -> Component:
        if not self._name:
            return ""

        return _render_icon(
            icon_path=f"{os.path.join(self.icons_dir, self._name)}.svg",
            class_=self._get_prop("class_"),
        )


def create_icon_base(icons_dir: str) -> type[Icon]:
    """
    Factory that returns an Icon subclass with ``icons_dir`` pre-configured.

    Example::

        BaseIcon = create_icon_base(icons_dir="/path/to/icons")

        # Usage — no subclassing needed:
        BaseIcon("calendar").class_("size-4")
        BaseIcon("user").class_("size-6")

    For multiple icon sets::

        OutlineIcon = create_icon_base(icons_dir="/path/to/outline")
        FilledIcon  = create_icon_base(icons_dir="/path/to/filled")
    """

    class _ConfiguredIcon(Icon):
        @property
        def icons_dir(self) -> str:
            return icons_dir

    # Give it a nicer repr
    _ConfiguredIcon.__qualname__ = "Icon"
    _ConfiguredIcon.__name__ = "Icon"

    return _ConfiguredIcon
