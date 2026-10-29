"""
What a docs page is made of.

Every page is declared in Python under pages/. A component page names the
class it documents, so its title, category, import line and props table come
from the class itself, and lists the panels that show it. An example is a
function returning a component, so the code a reader copies is the code that
rendered the preview.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from hue.types.core import ComponentType
from hue.ui.base import ChainableComponent
from hue_fastapi import HueFragmentsView, HueView

type Example = Callable[[], ComponentType]
type Layout = Literal["grid", "stack", "center"]
# The breakpoints a panel can start at, which layout/panel.py names the widths of.
type Viewport = Literal["sm", "md", "lg", "xl"]
type NoteKind = Literal["a11y", "note", "warn"]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def kebab(name: str) -> str:
    """
    TableOfContents becomes table-of-contents.
    """
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


@dataclass(frozen=True)
class Panel:
    """
    One framed specimen: a labelled canvas holding one or more examples.

    grid lays examples out as a state matrix, each under its caption; stack
    gives each the full width; center shows a single example in the middle of
    the canvas. min_height keeps room for an overlay that opens out of a small
    trigger, since the frame only grows with what is laid out in it. width
    starts the frame at a breakpoint instead of filling the panel, for a
    component that looks different above it.
    """

    label: str
    examples: tuple[Example, ...]
    hint: str = ""
    layout: Layout = "grid"
    min_height: int = 0
    captions: bool = True
    width: Viewport | None = None

    @property
    def slug(self) -> str:
        return slugify(self.label)


def panel(
    label: str,
    *examples: Example,
    hint: str = "",
    layout: Layout = "grid",
    min_height: int = 0,
    captions: bool = True,
    width: Viewport | None = None,
) -> Panel:
    """
    captions=False drops the name above each example, for examples that
    already say what they are, such as buttons labelled with their variant.
    """
    if not examples:
        raise ValueError(f"The {label!r} panel has no examples.")
    return Panel(
        label,
        examples,
        hint=hint,
        layout=layout,
        min_height=min_height,
        captions=captions,
        width=width,
    )


def caption(example: Example) -> str:
    """
    What a grid cell is called: the example function's name, read as words.
    """
    return example.__name__.replace("_", " ")


@dataclass(frozen=True)
class Note:
    """
    One row under a component's Notes heading, tagged by what it is.
    """

    kind: NoteKind
    text: str


@dataclass(frozen=True)
class ComponentPage:
    component: type[ChainableComponent]
    lede: str
    # The walkthrough: imports, the API in use, the gotchas. Built when the
    # page renders.
    usage: Callable[[], ComponentType] | None = None
    panels: list[Panel] = field(default_factory=list)
    # Composition parts with no page of their own, such as TableRow, whose
    # props are listed here instead.
    parts: list[type[ChainableComponent]] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    related: list[type[ChainableComponent]] = field(default_factory=list)
    # Views serving the page's live demos, mounted under /demos/<slug>/. A
    # HueView's index is served at /demos/<slug>/ itself.
    views: list[type[HueFragmentsView] | type[HueView]] = field(default_factory=list)

    def __post_init__(self) -> None:
        slugs = [p.slug for p in self.panels]
        if len(slugs) != len(set(slugs)):
            raise ValueError(f"{self.title} has two panels with the same label.")

    @property
    def title(self) -> str:
        return self.component.__name__

    @property
    def slug(self) -> str:
        return kebab(self.component.__name__)

    @property
    def href(self) -> str:
        return f"/components/{self.slug}/"

    @property
    def category(self) -> str:
        return self.component.category or "Other"


@dataclass(frozen=True)
class GuidePage:
    """
    A hand-written page that documents no single component.

    slug becomes the URL path, "" being the home page.
    """

    slug: str
    title: str
    nav_label: str
    group: str
    order: int
    build: Callable[[], ComponentType]

    @property
    def href(self) -> str:
        return "/" if self.slug == "" else f"/{self.slug}/"


@dataclass(frozen=True)
class NavItem:
    label: str
    href: str


@dataclass(frozen=True)
class NavGroup:
    title: str
    items: list[NavItem] = field(default_factory=list)
