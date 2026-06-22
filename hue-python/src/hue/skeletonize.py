"""
Turn a live component tree into a loading skeleton, and defer real content.

The win over DOM/pixel-based skeleton tools (Boneyard and friends) is that a
hue page is an introspectable tree of Python objects before any browser exists,
so mapping it to a skeleton is a tree transform rather than a measurement
problem. to_skeleton walks that tree: a component with its own skeleton() gives
an accurate placeholder, layout containers are preserved and recursed, and
anything unknown degrades to a single line.

defer pairs the skeleton with Alpine AJAX: render the skeleton instantly, then
fetch the real content into the same target. Because the skeleton is computed
from the same components every request, it never drifts out of sync the way a
generated static skeleton would.
"""

from __future__ import annotations

import copy
from typing import cast

from htmy import html

from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui.atoms.skeleton import Skeleton
from hue.ui.base import ChainableComponent


def _clone_with_children(
    node: ChainableComponent, children: list[Component]
) -> ChainableComponent:
    """
    Shallow-copy a container, swapping in skeletonised children.

    The copy shares the original's props/attrs (kept verbatim, so layout
    classes survive) and only its children are replaced — we never mutate the
    shared dicts, so the original is untouched.
    """
    clone = copy.copy(node)
    # A skeletonised child may itself be a fragment (tuple); htmy renders those
    # nested, so storing them as children is fine even though the slot is typed
    # as a single component.
    clone._children = cast("tuple[ComponentType, ...]", tuple(children))
    return clone


def _component_to_skeleton(node: ChainableComponent) -> Component:
    """
    Skeletonise a chainable component.

    An instance override (skeleton_as) wins outright, then a component-defined
    placeholder (an overridden _skeleton_impl). Otherwise the component is
    treated as a transparent container: its layout shell (Stack, html.div, ...)
    is kept and its children recursed. A childless component with neither falls
    back to a single line.
    """
    if isinstance(node, Skeleton):
        return node
    has_own_skeleton = (
        node._skeleton_override is not None
        or type(node)._skeleton_impl is not ChainableComponent._skeleton_impl
    )
    if has_own_skeleton:
        return node.skeleton()
    if node._children:
        return _clone_with_children(
            node, [to_skeleton(child) for child in node._children]
        )
    return node.skeleton()


def to_skeleton(node: Component) -> Component:
    """
    Map a component (sub)tree to its loading-skeleton equivalent.

    Strings become a line, sequences map element-wise, components dispatch
    through their skeleton() (see the helper), and raw/unknown nodes degrade to
    a single line.
    """
    if node is None or node is UNDEFINED:
        return UNDEFINED

    if isinstance(node, str):
        return Skeleton().shape("line") if node.strip() else UNDEFINED

    if isinstance(node, (list, tuple)):
        return cast(
            "tuple[ComponentType, ...]",
            tuple(to_skeleton(child) for child in node),
        )

    if isinstance(node, ChainableComponent):
        return _component_to_skeleton(node)

    # Raw htmy tags / unknown nodes: a plain line is the safe placeholder.
    return Skeleton().shape("line")


def defer(
    *,
    skeleton: Component,
    url: str,
    target: str,
    method: str = "get",
) -> Component:
    """
    Render a skeleton now and fetch the real content into its place.

    Returns a live region holding the skeleton; on init it issues an Alpine
    AJAX request to url and merges the response into the element with id
    target, so the handler at url should return its content wrapped in a
    matching element (e.g. HueResponse(component, target=target)).

    The region is a polite status with aria-busy set while loading and cleared
    once the content merges; the skeleton itself is decorative (aria-hidden).
    """
    return html.div(
        html.span("Loading…", class_="sr-only"),
        cast("ComponentType", skeleton),
        id=target,
        role="status",
        aria_live="polite",
        aria_busy="true",
        **{
            "x-init": f"$ajax('{url}', {{ method: '{method}', target: '{target}' }})",
            "@ajax:after": "$el.setAttribute('aria-busy', 'false')",
        },
    )
