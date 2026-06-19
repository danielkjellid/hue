from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Callable
from xml.etree import ElementTree as ET

from htmy import SafeStr, html

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames

#: An icon resolver turns an icon *name* into raw SVG markup.
#:
#: This is the single extension point that keeps hue from locking you into one
#: icon library. The bundled resolver reads ``.svg`` files from a directory, but
#: a resolver is just a function — it can load icons from a Python package's
#: resources, a sprite sheet, a remote service, an in-memory dict, or a
#: database. Whatever returns ``<svg>…</svg>`` works.
IconResolver = Callable[[str], str]

_SVG_NS = "http://www.w3.org/2000/svg"


def directory_resolver(icons_dir: str) -> IconResolver:
    """Build an :data:`IconResolver` that reads ``{icons_dir}/{name}.svg``.

    This is the resolver behind :func:`create_icon_base`'s ``icons_dir``
    argument — ``create_icon_base(icons_dir=path)`` is shorthand for
    ``create_icon_base(resolver=directory_resolver(path))``. Call it directly
    when you want the resolver as a value to wrap or compose.

    Reads are cached per process, so an icon is only ever read and parsed once
    no matter how many times it is rendered — a table with the same icon on a
    thousand rows costs a single file read.
    """
    base = os.path.abspath(icons_dir)

    def resolve(name: str) -> str:
        path = os.path.join(base, f"{name}.svg")
        try:
            return _read_file(path)
        except FileNotFoundError as e:
            raise RuntimeError(f"Icon '{name}' not found at {path}") from e

    return resolve


@lru_cache(maxsize=None)
def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _strip_namespaces(element: ET.Element) -> None:
    """Drop XML namespace prefixes from an element tree, in place.

    ``ElementTree`` reports a namespaced ``<svg>`` as ``{http://…}svg``. We strip
    the namespace from every tag and attribute so the tree re-serialises as
    plain ``<svg>``/``<path>``/… markup — which is exactly what an inline SVG in
    an HTML document needs (the browser assigns the SVG namespace itself).
    """
    if "}" in element.tag:
        element.tag = element.tag.split("}", 1)[1]
    for key in list(element.attrib):
        if "}" in key:
            element.attrib[key.split("}", 1)[1]] = element.attrib.pop(key)
    for child in element:
        _strip_namespaces(child)


@lru_cache(maxsize=None)
def _parse_icon(markup: str) -> tuple[dict[str, str], str]:
    """Parse, validate, and normalise SVG markup.

    Returns the root ``<svg>`` attributes (minus ``width``/``height`` so CSS can
    size the icon) and the inner markup as a string. The whole subtree is kept
    verbatim, so every SVG element — ``path``, ``circle``, ``rect``, ``line``,
    ``polyline``, ``polygon``, ``g``, ``title``, gradients, … — is preserved.

    Cached on the markup string: a given icon is parsed exactly once.
    """
    try:
        root = ET.fromstring(markup)
    except ET.ParseError as e:
        raise RuntimeError(f"Icon markup is not valid XML: {e}") from e

    _strip_namespaces(root)

    if root.tag != "svg":
        raise RuntimeError(
            f"Icon markup must have a single <svg> root, got <{root.tag}>"
        )

    if not root.get("viewBox"):
        raise RuntimeError("Icon <svg> is missing a viewBox attribute")

    # Hard-coded dimensions stop utility classes (e.g. size-4) from sizing it.
    root.attrib.pop("width", None)
    root.attrib.pop("height", None)

    inner = "".join(ET.tostring(child, encoding="unicode") for child in root)
    return dict(root.attrib), inner


def _format_attr_name(name: str) -> str:
    """Normalise an attribute key the way htmy's tag formatter does.

    ``class_`` -> ``class`` (trailing underscore stripped), ``aria_label`` ->
    ``aria-label`` (internal underscores hyphenated), ``viewBox`` and Alpine
    attributes (``@click``, ``:src``) pass through unchanged.
    """
    if name[:1] == "_" or name[-1:] == "_":
        return name.strip("_")
    return name.replace("_", "-")


def _svg_attrs(
    *, root_attrs: dict[str, str], base_attrs: dict[str, Any], class_: str | None
) -> dict[str, Any]:
    """Merge the source ``<svg>`` attributes with the component's own attributes.

    Component-level attributes (``.id()``, ``.aria_*()``, Alpine directives) win
    over whatever the source file declared, and classes are concatenated rather
    than replaced. Keys are normalised first so ``aria-hidden`` from the file and
    ``.aria_hidden()`` from the component collapse to a single attribute.
    """
    attrs: dict[str, Any] = {_format_attr_name(k): v for k, v in root_attrs.items()}

    source_class = attrs.pop("class", None)

    for key, value in base_attrs.items():
        attrs[_format_attr_name(key)] = value

    merged_class = classnames(source_class, class_)
    if merged_class:
        attrs["class"] = merged_class

    # Icons are decorative by default. Only mark them so when the caller hasn't
    # given the icon an accessible name or an explicit role.
    if not ({"aria-hidden", "aria-label", "role"} & attrs.keys()):
        attrs["aria-hidden"] = "true"

    # Inline SVG renders fine without it, but declaring the namespace keeps the
    # output valid if a page is ever served as XHTML or the markup extracted.
    attrs.setdefault("xmlns", _SVG_NS)
    return attrs


class Icon(ChainableComponent):
    """
    An inline SVG icon resolved from a pluggable icon source.

    hue does not ship an icon library — you bring your own. An icon's markup is
    inlined into the page (rather than referenced as an ``<img>``) so it can be
    sized and coloured with CSS: give it ``size-*`` utilities and use
    ``currentColor`` in the SVG so ``text-*`` classes set its colour.

    The whole SVG is preserved as-authored, so any icon set works — Lucide,
    Heroicons, Tabler, Feather, or your own — regardless of which elements
    (``path``, ``circle``, ``rect``, ``line``, ``g``, …) it uses. The only
    requirements are a single ``<svg>`` root and a ``viewBox``.

    Not instantiated directly — bind an icon source with
    :func:`create_icon_base`, then call the returned class with an icon name.

    Example::

        Icon = create_icon_base(icons_dir="/path/to/icons")
        Icon("calendar").class_("size-4 text-primary")
    """

    category = "Media"

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self._name = name

    @classmethod
    def example(cls) -> "Icon":
        """A representative instance, used by the docs site for previews."""
        icons_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "static", "icons")
        )
        return create_icon_base(icons_dir=icons_dir)("circle-info").class_("size-6")

    @property
    def resolver(self) -> IconResolver:
        raise NotImplementedError(
            "Icon has no icon source — create one with create_icon_base()"
        )

    def _render(self, context: HueContext) -> Component:
        if not self._name:
            return ""

        markup = self.resolver(self._name)
        root_attrs, inner = _parse_icon(markup)
        attrs = _svg_attrs(
            root_attrs=root_attrs,
            base_attrs=self._get_base_html_attrs(),
            class_=self._get_prop("class_"),
        )
        return html.svg(SafeStr(inner), **attrs)


def create_icon_base(
    icons_dir: str | None = None, *, resolver: IconResolver | None = None
) -> type[Icon]:
    """
    Bind an icon source and return an :class:`Icon` subclass that uses it.

    Pass ``icons_dir`` to load ``.svg`` files from a folder (the common case),
    or pass a custom ``resolver`` to load icons from anywhere::

        # From a directory of .svg files
        Icon = create_icon_base(icons_dir="/path/to/icons")
        Icon("calendar").class_("size-4")

        # Several icon sets side by side
        OutlineIcon = create_icon_base(icons_dir="/icons/outline")
        FilledIcon = create_icon_base(icons_dir="/icons/filled")

        # A custom source — here, icons shipped inside a Python package
        from importlib.resources import files

        def resolve(name: str) -> str:
            return (files("my_app.icons") / f"{name}.svg").read_text()

        Icon = create_icon_base(resolver=resolve)

    ``icons_dir`` is just shorthand: it calls :func:`directory_resolver` for
    you, so these two are equivalent::

        create_icon_base(icons_dir="/path/to/icons")
        create_icon_base(resolver=directory_resolver("/path/to/icons"))

    Use ``directory_resolver`` directly only when you want the resolver as a
    value to wrap or compose (e.g. a fallback between sets).
    """
    if resolver is None:
        if icons_dir is None:
            raise ValueError("Provide either icons_dir or a resolver")
        resolver = directory_resolver(icons_dir)

    bound_resolver = resolver

    class _ConfiguredIcon(Icon):
        @property
        def resolver(self) -> IconResolver:
            return bound_resolver

    # Give it a nicer repr
    _ConfiguredIcon.__qualname__ = "Icon"
    _ConfiguredIcon.__name__ = "Icon"

    return _ConfiguredIcon
