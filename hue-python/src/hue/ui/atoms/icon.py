from typing import Literal
from xml.dom import minidom

from htmy import ComponentType, Tag, html


__all__ = ["Icon"]


class path(Tag):
    __slots__ = ()


class circle(Tag):
    __slots__ = ()


IconName = Literal[
    "mail",
    "logo",
    "information",
    "moon",
    "sun",
    "menu",
    "close",
    "google",
]


def Icon(*, name: IconName, class_: str | None = None) -> ComponentType:
    """
    Render an SVG icon based on the name of the static svg file.
    """

    paths = []
    circles = []

    width, height, view_box, fill = None, None, None, None

    try:
        with open(_get_icon_path(name=name), "r") as f:
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
        raise RuntimeError(f"Icon {name} not found") from e

    if not view_box:
        raise RuntimeError(f"No viewBox found for icon {name}")

    if not paths and not circles:  # Allow either paths or circles
        raise RuntimeError(f"No paths or circles found for icon {name}")

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


def _get_icon_path(name: IconName) -> str:
    """
    Get the path to the icon file.
    """
    return ""
