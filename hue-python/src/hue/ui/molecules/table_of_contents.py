from __future__ import annotations

import json
import math
from typing import NamedTuple

from htmy import SafeStr, html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if


class Heading(NamedTuple):
    """
    One heading on the page, and how deep it sits.

    level is the heading's own level - 2 for an h2, 3 for an h3 - so a list
    built by walking the document keeps its shape without being renumbered.
    The shallowest level present is the top of the rail, whatever it is.
    """

    id: str
    label: str
    level: int = 2


# One entry is a row this tall, and the rail is drawn from that number: _ROW
# and _ROW_CLASS are the same 36px said twice, once to Python and once to
# Tailwind, and have to move together.
_ROW = 36
_ROW_CLASS = "h-9"

# What one level of nesting moves - the label and the rail by the same amount,
# so the rail keeps reading as the left edge of the text it belongs to.
_INDENT = 16

# The rail sits far enough in that the dot on it has room to its left: an SVG
# clips at its own edge, and a dot centred on x=0 would lose half of itself.
_RAIL_X = 5.0
_GAP = 18.0

# The vertical distance a change of level is spread over. Shorter than a row,
# so the curve starts and ends inside the gap between two entries rather than
# leaning against the text of either.
_BEND = 24.0

_STROKE = 1.5
_DOT = 4.0
_TERMINAL = 3.0

# The fill grows by uncovering more of a dash; the dot moves by travelling
# further along the path. Both are the same 300ms, so they arrive together.
_FILL_MOTION = "transition-[stroke-dashoffset] duration-300 ease-out"
_DOT_MOTION = "transition-[offset-distance] duration-300 ease-out"

_LINK = (
    "flex items-center rounded-md pe-2 font-ui text-sm font-medium "
    "text-fg-muted no-underline hover:text-fg "
    "aria-[current=location]:font-semibold aria-[current=location]:text-fg"
)


class TableOfContents(ChainableComponent):
    """
    The headings on this page, with the reading position marked on a rail.

    The rail bends to follow the nesting, and fills in as far as the heading
    being read - which follows the page as it scrolls. current() is where that
    starts, and where it stays when none of the headings are on this page.

    Entries are one row each: the rail is drawn from the row height, so a long
    heading is truncated rather than wrapped.
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .current("components")
            .items(
                [
                    Heading("introduction", "Introduction"),
                    Heading("core-concepts", "Core Concepts"),
                    Heading("architecture", "Architecture", 3),
                    Heading("data-flow", "Data Flow", 3),
                    Heading("components", "Components"),
                    Heading("button", "Button", 3),
                    Heading("card", "Card", 3),
                    Heading("utilities", "Utilities"),
                ]
            )
        )

    def items(self, value: list[Heading] | list[tuple[str, str, int]]) -> Self:
        """
        The headings, in the order they appear on the page.

        Heading(id, label, level), or the plain tuple it unpacks from. The id
        is the element the entry scrolls to.
        """
        self._props["items"] = value
        return self

    def current(self, value: str) -> Self:
        """
        The id of the heading to start at, for a page rendered part way down.
        """
        self._props["current"] = value
        return self

    def title(self, value: str) -> Self:
        """
        What the list is called. It names the navigation too, so a page with
        more than one set of links says which is which.
        """
        self._props["title"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        items = [Heading(*item) for item in self._get_prop("items", [])]
        title: str = self._get_prop("title", "On this page")
        current: str | None = self._get_prop("current")

        rail = _rail([item.level for item in items])
        ids = [item.id for item in items]
        active = ids.index(current) if current in ids else 0
        title_id = "$id('hue-toc-title')"

        return html.nav(
            html.div(
                HueIcon("file-text").class_("size-3.5 flex-none text-fg-subtle"),
                html.span(title),
                class_=(
                    "mb-1 flex items-center gap-2 font-ui text-2xs font-bold "
                    "uppercase tracking-[0.05em] text-fg-subtle"
                ),
                **{":id": title_id},
            ),
            html.div(
                # render_if rather than render_when: with nothing to draw there
                # is no rail, and _svg has no first point to start one at.
                render_if(items or None, lambda _: _svg(rail, active)),
                html.ol(
                    *(
                        _entry(item, rail.xs[index], index == active, index)
                        for index, item in enumerate(items)
                    ),
                    class_="m-0 list-none p-0",
                ),
                class_="relative",
            ),
            class_=classnames("w-full", self._get_prop("class_")),
            **{
                ":aria-labelledby": title_id,
                "x-id": "['hue-toc-title']",
                "x-data": (
                    f"hueToc({_ids_source(ids)}, {active}, {rail.reach_source()})"
                ),
                **self._get_base_html_attrs(),
            },
        )


def _entry(item: Heading, x: float, current: bool, index: int) -> ComponentType:
    """
    One heading, as a real link to the section it names.

    aria-current="location" rather than "page": every entry points at this
    page, and what is being marked is where in it the reader has got to.
    """
    return html.li(
        html.a(
            html.span(item.label, class_="truncate"),
            href=f"#{item.id}",
            class_=classnames(_ROW_CLASS, _LINK, FOCUS_RING),
            style=f"padding-inline-start: {x + _GAP:g}px",
            **{
                "aria_current": "location" if current else None,
                ":aria-current": f"active === {index} ? 'location' : null",
            },
        ),
        class_="m-0",
    )


def _svg(rail: _Rail, active: int) -> ComponentType:
    """
    The rail: the line itself, the fill up to where the reader is, and the
    three dots on it - one at each end and one where they are.

    The fill is a second copy of the same path, dashed so that exactly the
    first n pixels of it show, which is how a stroke is animated along a
    curve. The moving dot rides the path with offset-path for the same
    reason: given the two endpoints and nothing else, it would cut the corner
    of every bend instead of following it.

    htmy models no SVG children, so this is built as markup. Every value in
    it is computed from the levels, never from caller text.
    """
    reach = rail.reach[active]
    last = len(rail.reach) - 1
    line = f"d='{rail.d}' fill='none' stroke-width='{_STROKE:g}' stroke-linecap='round'"

    markup = (
        f"<path {line} class='stroke-border'></path>"
        f"<path {line} class='stroke-accent {_FILL_MOTION}'"
        f" stroke-dasharray='{rail.length:.2f}'"
        f" stroke-dashoffset='{rail.length - reach:.2f}'"
        f' :stroke-dashoffset="length - reach[active]"></path>'
        f"<circle cx='{rail.xs[0]:g}' cy='{rail.ys[0]:g}'"
        f" r='{_TERMINAL:g}' class='fill-accent'></circle>"
        f"<circle cx='{rail.xs[last]:g}' cy='{rail.ys[last]:g}'"
        f" r='{_TERMINAL:g}' class='fill-border'></circle>"
        f"<circle r='{_DOT:g}' class='fill-accent {_DOT_MOTION}'"
        f" style=\"offset-path: path('{rail.d}');"
        f' offset-distance: {_percent(reach, rail.length):g}%"'
        f" :style=\"{{ offsetDistance: at + '%' }}\"></circle>"
    )

    return html.svg(
        SafeStr(markup),
        width=f"{rail.width:g}",
        height=f"{rail.height:g}",
        aria_hidden="true",
        class_="pointer-events-none absolute start-0 top-0",
    )


class _Rail(NamedTuple):
    """
    Everything the drawing needs, worked out from the levels alone.
    """

    d: str
    reach: list[float]
    xs: list[float]
    ys: list[float]
    length: float
    width: float
    height: float

    def reach_source(self) -> str:
        """
        The distances as an Alpine array literal, rounded to the pixel we can
        actually see.
        """
        return json.dumps([round(value, 2) for value in self.reach])


def _rail(levels: list[int]) -> _Rail:
    """
    The path down the side, and how far along it each entry sits.

    Straight between two entries at the same level, and an S between two that
    are not: a cubic whose control points are directly below the one and above
    the other leaves the curve vertical where it meets the line, so the joins
    do not show.
    """
    top = min(levels, default=0)
    xs = [_RAIL_X + (level - top) * _INDENT for level in levels]
    ys = [index * _ROW + _ROW / 2 for index in range(len(levels))]

    commands: list[str] = []
    reach: list[float] = []
    length = 0.0

    if xs:
        commands.append(f"M {xs[0]:g} {ys[0]:g}")
        reach.append(0.0)

    for index in range(1, len(xs)):
        x0, y0, x1, y1 = xs[index - 1], ys[index - 1], xs[index], ys[index]
        if x0 == x1:
            commands.append(f"L {x1:g} {y1:g}")
            length += y1 - y0
        else:
            middle = (y0 + y1) / 2
            start, end = middle - _BEND / 2, middle + _BEND / 2
            commands.append(f"L {x0:g} {start:g}")
            commands.append(f"C {x0:g} {middle:g} {x1:g} {middle:g} {x1:g} {end:g}")
            commands.append(f"L {x1:g} {y1:g}")
            length += (start - y0) + (y1 - end)
            length += _curve_length((x0, start), (x0, middle), (x1, middle), (x1, end))
        reach.append(length)

    return _Rail(
        d=" ".join(commands),
        reach=reach,
        xs=xs,
        ys=ys,
        length=length,
        width=max(xs, default=0.0) + _DOT + 1,
        height=len(levels) * _ROW,
    )


def _curve_length(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    *,
    samples: int = 24,
) -> float:
    """
    How long a cubic is, close enough to put a dot on it.

    Flattened rather than solved, because the closed form does not exist. The
    fill and the dot both ride this one number, so they agree with each other
    whatever it is - and at this size the error is a hundredth of a pixel.
    """

    def point(t: float) -> tuple[float, float]:
        u = 1 - t
        return (
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        )

    total = 0.0
    previous = point(0.0)
    for step in range(1, samples + 1):
        current = point(step / samples)
        total += math.hypot(current[0] - previous[0], current[1] - previous[1])
        previous = current
    return total


def _percent(value: float, of: float) -> float:
    return 0.0 if of == 0 else round(value / of * 100, 3)


def _ids_source(ids: list[str]) -> str:
    """
    The ids as an Alpine array literal.

    Quoted with json.dumps rather than by hand: an id is a caller's string,
    and an apostrophe in one would otherwise end the literal early and leave
    the rest of it to be evaluated.
    """
    return json.dumps(ids)
