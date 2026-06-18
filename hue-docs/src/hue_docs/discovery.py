"""Introspect ``hue.ui`` to discover components and their showcase-able modifiers.

Every component is a :class:`~hue.ui.base.ChainableComponent`. Its visual
"axes" are modifier methods whose single argument is a ``Literal`` (an enum like
``variant``/``size``) or a ``bool`` (a toggle like ``disabled``). We resolve
those annotations — including PEP 695 ``type X = Literal[...]`` aliases — to
build a variant grid automatically, so a brand-new component shows up in the
docs without anyone writing an example for it.
"""

from __future__ import annotations

import inspect
import re
import typing
from dataclasses import dataclass, field
from typing import Any, Literal

from hue import ui
from hue.ui.base import ChainableComponent

# Modifier names defined on the base class (class_, id, aria_*, x_*, content, ...)
# are shared chrome, not per-component visual axes — skip them.
_BASE_METHOD_NAMES = frozenset(dir(ChainableComponent))

_GET_PROP_RE = re.compile(
    r"""_get_prop\(\s*["'](?P<name>\w+)["']\s*,\s*(?P<default>[^),]+)\)"""
)


@dataclass(frozen=True)
class Axis:
    """A single showcase-able modifier of a component."""

    method: str
    kind: Literal["enum", "bool"]
    values: list[Any]
    default: Any | None = None


@dataclass(frozen=True)
class ComponentDoc:
    name: str
    cls: type[ChainableComponent]
    paragraphs: list[str] = field(default_factory=list)
    axes: list[Axis] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.name.lower()


def _unwrap_alias(annotation: Any) -> Any:
    """Resolve PEP 695 / plain type aliases down to the underlying type."""
    seen = 0
    while isinstance(annotation, typing.TypeAliasType) and seen < 10:
        annotation = annotation.__value__
        seen += 1
    return annotation


def _axis_for_method(cls: type[ChainableComponent], name: str) -> Axis | None:
    func = getattr(cls, name)
    if not inspect.isfunction(func):
        return None

    try:
        # eval_str resolves the string annotations created by
        # `from __future__ import annotations` using the method's own module.
        signature = inspect.signature(func, eval_str=True)
    except (TypeError, ValueError, NameError):
        return None

    params = [p for p in signature.parameters.values() if p.name != "self"]
    if len(params) != 1:
        return None

    annotation = _unwrap_alias(params[0].annotation)

    if annotation is bool:
        return Axis(method=name, kind="bool", values=[False, True])

    if typing.get_origin(annotation) is Literal:
        values = list(typing.get_args(annotation))
        if values:
            return Axis(method=name, kind="enum", values=values)

    return None


def _defaults_from_render(cls: type[ChainableComponent]) -> dict[str, str]:
    """Best-effort: read ``_get_prop("x", <default>)`` defaults from ``_render``."""
    try:
        source = inspect.getsource(cls._render)
    except (OSError, TypeError):
        return {}

    defaults: dict[str, str] = {}
    for match in _GET_PROP_RE.finditer(source):
        defaults[match.group("name")] = match.group("default").strip().strip("\"'")
    return defaults


def _paragraphs(cls: type[ChainableComponent]) -> list[str]:
    doc = inspect.getdoc(cls) or ""
    paragraphs: list[str] = []
    for block in doc.split("\n\n"):
        # Collapse whitespace and drop reStructuredText inline-literal markers
        # (``code`` -> code) so docstrings read cleanly as prose.
        text = " ".join(block.split()).replace("``", "")
        if not text:
            continue
        if text.startswith("Example") or text.startswith("Note:"):
            break
        paragraphs.append(text)
    return paragraphs


def _build_doc(name: str, cls: type[ChainableComponent]) -> ComponentDoc:
    defaults = _defaults_from_render(cls)
    axes: list[Axis] = []
    for method_name in sorted(set(dir(cls)) - _BASE_METHOD_NAMES):
        if method_name.startswith("_"):
            continue
        axis = _axis_for_method(cls, method_name)
        if axis is None:
            continue
        default = defaults.get(axis.method)
        if default is not None:
            axis = Axis(axis.method, axis.kind, axis.values, default=default)
        axes.append(axis)

    return ComponentDoc(
        name=name,
        cls=cls,
        paragraphs=_paragraphs(cls),
        axes=axes,
    )


def discover() -> list[ComponentDoc]:
    """Return a doc model for every documentable component exported from ``hue.ui``.

    A component is documented only if it provides an ``example()`` classmethod —
    that is the showcase entrypoint (its preview and usage snippet). Components
    without one (e.g. table subcomponents like ``TableRow`` that only make sense
    nested) are exported for composition but skipped here.
    """
    docs: list[ComponentDoc] = []
    for name in ui.__all__:
        obj = getattr(ui, name)
        if not (inspect.isclass(obj) and issubclass(obj, ChainableComponent)):
            continue
        if obj is ChainableComponent or inspect.isabstract(obj):
            continue
        if not callable(getattr(obj, "example", None)):
            continue
        docs.append(_build_doc(name, obj))

    docs.sort(key=lambda d: d.name)
    return docs
