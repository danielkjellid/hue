"""
Introspect hue.ui to discover components and their showcase-able modifiers.

Every component is a ChainableComponent. Its visual "axes" are modifier methods
whose single argument is a Literal (an enum like variant or size) or a bool (a
toggle like disabled). Those annotations, including PEP 695 type aliases, are
resolved to build a variant grid automatically, so a new component shows up in
the docs without anyone writing an example for it.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import typing
from dataclasses import dataclass, field
from typing import Any, Literal

from hue import ui
from hue.ui.base import ChainableComponent

# Modifier names defined on the base class (class_, id, aria_*, x_*, content, ...)
# are shared chrome, not per-component visual axes, so they are skipped.
_BASE_METHOD_NAMES = frozenset(dir(ChainableComponent))


@dataclass(frozen=True)
class Axis:
    """
    A single showcase-able modifier of a component.
    """

    method: str
    kind: Literal["enum", "bool"]
    values: list[Any]
    default: Any | None = None


@dataclass(frozen=True)
class ComponentDoc:
    name: str
    cls: type[ChainableComponent]
    category: str
    paragraphs: list[str] = field(default_factory=list)
    axes: list[Axis] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.name.lower()

    @property
    def href(self) -> str:
        return f"/components/{self.slug}/"


def _unwrap_alias(annotation: Any) -> Any:
    """
    Resolve PEP 695 type aliases down to the underlying type.
    """
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


def _render_source(cls: type[ChainableComponent]) -> str | None:
    try:
        return textwrap.dedent(inspect.getsource(cls._render))
    except (OSError, TypeError):
        return None


def _defaults(cls: type[ChainableComponent]) -> dict[str, Any]:
    """
    A component's prop defaults.

    Read from the literal default in every _get_prop("name", <literal>) call in
    _render (via the AST, so the shape of the call does not matter), then
    overlaid with whatever the constructor pre-sets in _props, which is how
    EmailInput gets autocomplete="email".
    """
    defaults: dict[str, Any] = {}

    source = _render_source(cls)
    if source is not None:
        for node in ast.walk(ast.parse(source)):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_get_prop"
                and len(node.args) == 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and isinstance(node.args[1], ast.Constant)
            ):
                continue
            defaults[node.args[0].value] = node.args[1].value

    try:
        defaults.update(cls()._props)
    except TypeError:
        pass

    return defaults


def _paragraphs(cls: type[ChainableComponent]) -> list[str]:
    """
    The docstring as prose paragraphs, dropping indented code samples and
    stopping at an Example section.
    """
    doc = inspect.getdoc(cls) or ""
    paragraphs: list[str] = []
    for block in doc.split("\n\n"):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if all(line[0].isspace() for line in lines):
            continue
        text = " ".join(block.split())
        if text.startswith("Example"):
            break
        paragraphs.append(text)
    return paragraphs


def _build_doc(name: str, cls: type[ChainableComponent], category: str) -> ComponentDoc:
    defaults = _defaults(cls)
    axes: list[Axis] = []
    for method_name in sorted(set(dir(cls)) - _BASE_METHOD_NAMES):
        if method_name.startswith("_"):
            continue
        axis = _axis_for_method(cls, method_name)
        if axis is None:
            continue
        axes.append(
            Axis(axis.method, axis.kind, axis.values, default=defaults.get(axis.method))
        )

    return ComponentDoc(
        name=name,
        cls=cls,
        category=category,
        paragraphs=_paragraphs(cls),
        axes=axes,
    )


def documented_components() -> dict[str, type[ChainableComponent]]:
    """
    Every component exported from hue.ui that gets its own docs page.

    A component opts out by setting category to None, which marks it as a
    composition-only part (a table row, say) that only makes sense nested.
    """
    components: dict[str, type[ChainableComponent]] = {}
    for name in ui.__all__:
        obj = getattr(ui, name)
        if not (inspect.isclass(obj) and issubclass(obj, ChainableComponent)):
            continue
        if obj is ChainableComponent or inspect.isabstract(obj):
            continue
        if obj.category is None:
            continue
        components[name] = obj
    return components


def discover() -> list[ComponentDoc]:
    """
    A doc model for every documented component, sorted by name.

    A documented component must define example(); it is the showcase entry
    point (preview and usage snippet), so a missing one fails the build loudly
    rather than silently dropping the component from the site.
    """
    docs: list[ComponentDoc] = []
    for name, cls in documented_components().items():
        if not callable(getattr(cls, "example", None)):
            raise TypeError(
                f"{name} is exported from hue.ui but defines no example() "
                "classmethod. Add one, or set category = None if it is a "
                "composition-only part."
            )
        assert cls.category is not None
        docs.append(_build_doc(name, cls, cls.category))

    docs.sort(key=lambda d: d.name)
    return docs
