"""Shared data models for the docs build (navigation + prose pages)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from hue.types.core import ComponentType


@dataclass(frozen=True)
class ProsePage:
    """A hand-written, non-component documentation page.

    ``slug`` becomes the URL path (``""`` is the home page at ``/``). ``build``
    is a zero-arg factory that returns the page's main content as a hue
    component, so construction is deferred until render time.
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
