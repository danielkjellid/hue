"""Showcase model + optional per-component examples.

A component's docs page is a list of :class:`Showcase` blocks, each holding a
set of :class:`Variant` cards (a rendered component + the code that produced it).

Examples are *optional*: drop a module in ``hue_docs/examples/`` exporting either
``EXAMPLE`` (one :class:`ComponentExample`) or ``EXAMPLES`` (a ``{class_name:
ComponentExample}`` mapping). Components without an example fall back to
:func:`auto_showcases`, which builds a grid straight from the discovered axes.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from hue.types.core import ComponentType

from hue_docs import examples as _examples_pkg
from hue_docs.discovery import ComponentDoc

Layout = Literal["row", "grid", "stack"]


@dataclass(frozen=True)
class Variant:
    """A single rendered example and the source that produced it."""

    label: str
    build: Callable[[], ComponentType]
    code: str


@dataclass(frozen=True)
class Showcase:
    title: str
    variants: list[Variant]
    description: str | None = None
    layout: Layout = "grid"


@dataclass(frozen=True)
class PlaygroundSpec:
    """Declares an interactive playground for a component.

    ``build`` returns a fresh base instance (with its content set). ``props``
    lists the modifier methods to expose as controls — empty means "every
    discovered enum/bool axis". The option lists and defaults for each prop are
    resolved from discovery at build time, so this stays terse.
    """

    build: Callable[[], ComponentType]
    ctor_code: str
    content_code: str = ""
    props: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentExample:
    showcases: list[Showcase] = field(default_factory=list)
    playground: PlaygroundSpec | None = None


def _format_call(method: str, value: Any) -> str:
    if isinstance(value, bool):
        return f".{method}()" if value else ""
    if isinstance(value, str):
        return f'.{method}("{value}")'
    return f".{method}({value!r})"


def axis_grid(
    title: str,
    *,
    ctor_code: str,
    build: Callable[[], Any],
    method: str,
    values: list[Any],
    content_code: str = "",
    description: str | None = None,
    layout: Layout = "grid",
) -> Showcase:
    """Build a :class:`Showcase` that varies a single modifier across *values*.

    ``build`` returns a fresh base instance; the modifier is then applied to it.
    The displayed code is ``{ctor_code}{call}{content_code}`` so it reads in the
    conventional modifier-before-content order.
    """
    variants: list[Variant] = []
    for value in values:

        def make(value: Any = value) -> ComponentType:
            instance = build()
            getattr(instance, method)(value)
            return instance

        label = "default" if value is False else str(value)
        code = f"{ctor_code}{_format_call(method, value)}{content_code}"
        variants.append(Variant(label=label, build=make, code=code))

    return Showcase(
        title=title,
        variants=variants,
        description=description,
        layout=layout,
    )


def auto_showcases(doc: ComponentDoc) -> list[Showcase]:
    """Fallback showcases for a component that has no example module."""
    showcases: list[Showcase] = []
    for axis in doc.axes:
        values = axis.values if axis.kind == "enum" else [False, True]

        variants: list[Variant] = []
        for value in values:

            def make(value: Any = value, method: str = axis.method) -> ComponentType:
                instance = doc.cls()
                getattr(instance, method)(value)
                return instance

            label = "default" if value is False else str(value)
            code = f"{doc.name}(){_format_call(axis.method, value)}"
            variants.append(Variant(label=label, build=make, code=code))

        showcases.append(
            Showcase(
                title=axis.method.replace("_", " ").title(),
                variants=variants,
                layout="stack",
            )
        )
    return showcases


def load_examples() -> dict[str, ComponentExample]:
    """Import every module under ``hue_docs.examples`` and collect its examples."""
    found: dict[str, ComponentExample] = {}
    for module_info in pkgutil.iter_modules(_examples_pkg.__path__):
        module = importlib.import_module(f"{_examples_pkg.__name__}.{module_info.name}")
        mapping: dict[str, ComponentExample] | None = getattr(module, "EXAMPLES", None)
        if mapping:
            found.update(mapping)
        single: ComponentExample | None = getattr(module, "EXAMPLE", None)
        component: type | None = getattr(module, "COMPONENT", None)
        if single is not None and component is not None:
            found[component.__name__] = single
    return found
