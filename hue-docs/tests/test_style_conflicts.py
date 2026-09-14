"""
No two classes on one element may fight over the same CSS property.

Two utilities setting one property resolve by stylesheet order, not by the order
they are written in the class list, so whichever Tailwind happens to emit last
wins and the intended one loses in silence - valid markup, no error, wrong
pixels. It has bitten this repo twice: a shared border-transparent on Button
beat the outline variants' colours, and a checkbox's error border lost to its
resting grey, leaving an invalid field with no visual state at all.

The fix is always the same: pick one in Python rather than layering them in the
class list.
"""

from __future__ import annotations

import collections
import html as html_lib
import re

import pytest
from hue.assets import css_built_path

from hue_docs.discovery import discover
from hue_docs.registry import auto_showcases, example_instance
from hue_docs.render import render_html_sync
from hue_docs.showcase import curated_showcases

_CSS = css_built_path().read_text()


def _declarations(token: str) -> dict[str, str]:
    """The properties a bare utility sets, mapped to their values."""
    escaped = "".join(c if (c.isalnum() or c in "-_") else "\\" + c for c in token)
    match = re.search(r"\n\s*\." + re.escape(escaped) + r"\s*\{([^}]*)\}", _CSS)
    if match is None:
        return {}

    found = {}
    for declaration in match.group(1).split(";"):
        prop, _, value = declaration.partition(":")
        prop = prop.strip()
        if value and not prop.startswith("--"):
            found[prop] = value.strip()
    return found


def _competing(class_attr: str) -> dict[str, list[str]]:
    by_property: dict[str, list[str]] = collections.defaultdict(list)
    composed: set[str] = set()

    for token in html_lib.unescape(class_attr).split():
        # hover:, focus-visible: and friends carry their own specificity, so
        # they are meant to win and are not in competition.
        if ":" in token:
            continue
        for prop, value in _declarations(token).items():
            if prop == "box-shadow":
                # Assembled from separate --tw-* slots for ring, shadow, inset.
                continue
            if "var(--tw-" in value:
                # Tailwind composes these deliberately - text-sm defers its
                # line-height to leading-none through --tw-leading - so the
                # winner is by design rather than by emission order.
                composed.add(prop)
            by_property[prop].append(token)

    return {
        prop: tokens
        for prop, tokens in by_property.items()
        if len(tokens) > 1 and prop not in composed
    }


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_no_two_classes_fight_over_the_same_property(doc):
    rendered = [example_instance(doc)]
    for showcase in curated_showcases(doc) + auto_showcases(doc):
        rendered += [variant.build() for variant in showcase.variants]

    clashes: dict[str, set[str]] = collections.defaultdict(set)
    for component in rendered:
        for attr in re.findall(r'class="([^"]*)"', render_html_sync(component)):
            for prop, tokens in _competing(attr).items():
                clashes[prop].add(" and ".join(sorted(tokens)))

    assert not clashes, (
        f"{doc.name} renders classes that compete for the same property, so which "
        f"one applies depends on the order Tailwind emitted them: "
        + "; ".join(
            f"{prop} ({', '.join(sorted(pairs))})" for prop, pairs in clashes.items()
        )
        + ". Pick one in Python instead of layering them in the class list."
    )
