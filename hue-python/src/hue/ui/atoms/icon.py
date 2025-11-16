import os
from dataclasses import dataclass
from xml.dom import minidom

from htmy import Tag, html
from typing_extensions import Any

from hue.context import HueContext
from hue.types.core import BaseComponent


class path(Tag):
    __slots__ = ()


class circle(Tag):
    __slots__ = ()


@dataclass(slots=True, frozen=True, kw_only=True)
class HueIcon(BaseComponent):
    name: str

    @property
    def icons_dir(self) -> str:
        raise NotImplementedError("Icons dir must be specified")

    def htmy(self, context: HueContext, **kwargs: Any) -> html.svg:
        return _render_icon(
            icon_path=f"{os.path.join(self.icons_dir, self.name)}.svg",
            class_=self.class_,
        )


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
                    "d": path.getAttribute("d"),
                    "stroke": path.getAttribute("stroke"),
                    "stroke-linecap": path.getAttribute("stroke-linecap"),
                    "stroke-linejoin": path.getAttribute("stroke-linejoin"),
                    "stroke-width": path.getAttribute("stroke-width"),
                    "fill": path.getAttribute("fill"),
                }
                for path in icon_doc.getElementsByTagName("path")
            ]

            circles = [
                {
                    "cx": circle.getAttribute("cx"),
                    "cy": circle.getAttribute("cy"),
                    "r": circle.getAttribute("r"),
                    "fill": circle.getAttribute("fill"),
                    "stroke": circle.getAttribute("stroke"),
                    "stroke-linecap": circle.getAttribute("stroke-linecap"),
                    "stroke-linejoin": circle.getAttribute("stroke-linejoin"),
                    "stroke-width": circle.getAttribute("stroke-width"),
                }
                for circle in icon_doc.getElementsByTagName("circle")
            ]
    except FileNotFoundError as e:
        raise RuntimeError(f"Icon at {path} not found") from e

    if not view_box:
        raise RuntimeError(f"No viewBox found for icon at {path}")

    if not paths and not circles:  # Allow either paths or circles
        raise RuntimeError(f"No paths or circles found for icon at {path}")

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
