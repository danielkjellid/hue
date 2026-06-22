from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable, ClassVar, cast, override
from xml.etree import ElementTree as ET

from htmy import Formatter, Properties, PropertyValue, SafeStr, html

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.skeleton import Skeleton
from hue.ui.base import ChainableComponent
from hue.utils import classnames

# An icon resolver turns an icon name into raw SVG markup. It is just a
# function, which is what keeps hue from locking you into one icon set: icons
# can come from a directory, a Python package, a sprite, a dict, or a remote
# service — anything that returns an <svg> string.
IconResolver = Callable[[str], str]

_SVG_NS = "http://www.w3.org/2000/svg"

# Bound the read/parse caches. A static icon set never approaches this, so the
# icons in use stay hot; the cap only matters for a dynamic resolver returning
# ever-varying markup, where an unbounded cache would grow without limit. On
# overflow the LRU just evicts and re-reads/re-parses.
_CACHE_SIZE = 512


def directory_resolver(icons_dir: str) -> IconResolver:
    """
    Build a resolver that reads icons from {icons_dir}/{name}.svg.

    Reads are cached per process, so an icon with the same name is read once no
    matter how many times it renders.
    """
    base = os.path.abspath(icons_dir)

    def resolve(name: str) -> str:
        path = os.path.join(base, f"{name}.svg")
        try:
            return _read_file(path)
        except FileNotFoundError as e:
            raise RuntimeError(f"Icon '{name}' not found at {path}") from e

    return resolve


@lru_cache(maxsize=_CACHE_SIZE)
def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _strip_namespaces(element: ET.Element) -> None:
    """
    Drop XML namespace prefixes from a parsed element tree, in place.

    ElementTree reports a namespaced svg root as {http://...}svg. Stripping the
    prefix lets the tree re-serialise as plain svg/path/... markup, which is what
    an inline SVG needs — the browser supplies the namespace itself.
    """
    if "}" in element.tag:
        element.tag = element.tag.split("}", 1)[1]
    for key in list(element.attrib):
        if "}" in key:
            element.attrib[key.split("}", 1)[1]] = element.attrib.pop(key)
    for child in element:
        _strip_namespaces(child)


@lru_cache(maxsize=_CACHE_SIZE)
def _parse_icon(markup: str) -> tuple[dict[str, str], str]:
    """
    Parse, validate, and normalise SVG markup.

    Returns the root svg attributes (minus width/height, so CSS utilities can
    size the icon) and its inner markup. The subtree is kept verbatim, so any
    SVG element survives. Cached on the markup string.
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
    _ = root.attrib.pop("width", None)
    _ = root.attrib.pop("height", None)

    inner = "".join(ET.tostring(child, encoding="unicode") for child in root)
    return dict(root.attrib), inner


# htmy rewrites attribute names at render time (aria_label -> aria-label, and so
# on), so reuse its formatter here to normalise the keys we merge — they then
# match exactly what htmy emits, instead of relying on a reimplementation that
# could drift. The Alpine/AJAX mixins store their attrs pre-hyphenated (x-data,
# @click, :src), so in practice only aria_* keys are ever rewritten.
_format_attr_name = Formatter().format_name


def _svg_attrs(
    *, root_attrs: dict[str, str], base_attrs: Properties, class_: str | None
) -> dict[str, PropertyValue]:
    """
    Merge the source svg attributes with the component's own.

    Component attributes (id, aria, Alpine directives) win over whatever the
    source file declared, and classes are concatenated rather than replaced.
    Keys are normalised first, so aria-hidden from the file and aria_hidden from
    the component collapse into one attribute.
    """
    attrs: dict[str, PropertyValue] = {
        _format_attr_name(k): v for k, v in root_attrs.items()
    }

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
    if "xmlns" not in attrs:
        attrs["xmlns"] = _SVG_NS
    return attrs


class Icon(ChainableComponent):
    """
    An inline SVG icon resolved from a pluggable icon source.

    hue ships no icons — you bring your own. The markup is inlined rather than
    referenced as an img, so CSS can drive it: size it with size-* utilities and
    use currentColor in the SVG so text-* classes set its colour. The SVG is kept
    as-authored, so any set works (Lucide, Heroicons, Tabler, ...); the only
    requirements are a single svg root and a viewBox.

    Don't instantiate directly. Bind a source with create_icon_base, then call
    the returned class with an icon name:

        Icon = create_icon_base(icons_dir="/path/to/icons")
        Icon("calendar").class_("size-4 text-primary")
    """

    category: ClassVar[str] = "Media"

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self._name: str = name

    @classmethod
    def example(cls) -> "Icon":
        """
        A representative instance, used by the docs site for previews.
        """
        icons_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "static", "icons")
        )
        return create_icon_base(icons_dir=icons_dir)("circle-info").class_("size-6")

    @property
    def resolver(self) -> IconResolver:
        raise NotImplementedError(
            "Icon has no icon source — create one with create_icon_base()"
        )

    @override
    def _render(self, context: HueContext[object]) -> Component:
        if not self._name:
            return ""

        markup = self.resolver(self._name)
        root_attrs, inner = _parse_icon(markup)
        attrs = _svg_attrs(
            root_attrs=root_attrs,
            base_attrs=self._get_base_html_attrs(),
            class_=cast("str | None", self._get_prop("class_")),
        )
        return html.svg(SafeStr(inner), **attrs)

    @override
    def _skeleton_impl(self) -> Component:
        return Skeleton().shape("rect").width("w-5").height("h-5").rounded("rounded-md")


def create_icon_base(
    icons_dir: str | None = None, *, resolver: IconResolver | None = None
) -> type[Icon]:
    """
    Bind an icon source and return an Icon subclass that uses it.

    Pass icons_dir to load .svg files from a folder (the common case), or pass a
    resolver to load icons from anywhere. icons_dir is just shorthand for
    resolver=directory_resolver(dir); reach for directory_resolver yourself only
    when you want the resolver as a value to wrap or compose.

        Icon = create_icon_base(icons_dir="/path/to/icons")
        Icon("calendar").class_("size-4")
    """
    if resolver is None:
        if icons_dir is None:
            raise ValueError("Provide either icons_dir or a resolver")
        resolver = directory_resolver(icons_dir)

    bound_resolver = resolver

    class _ConfiguredIcon(Icon):
        @property
        @override
        def resolver(self) -> IconResolver:
            return bound_resolver

    # Give it a nicer repr
    _ConfiguredIcon.__qualname__ = "Icon"
    _ConfiguredIcon.__name__ = "Icon"

    return _ConfiguredIcon
