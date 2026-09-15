"""
hue honours a request for less motion.

Every animation and transition in the system comes from the stylesheet, so
one blanket rule covers all of them - and a component added later cannot
forget to opt in. Asserted against the built stylesheet because the rule is
easy to lose in a refactor and nothing else would notice: the animations
would simply keep playing for the people who asked them not to.
"""

from __future__ import annotations

import re

import pytest

# Not zero: a 0.01ms duration still fires transitionend and animationend, so
# anything waiting on one to remove an element or hand focus over keeps
# working. Zero would leave those listeners waiting forever.
REQUIRED = (
    "animation-duration: 0.01ms",
    "animation-iteration-count: 1",
    "transition-duration: 0.01ms",
    "scroll-behavior: auto",
)


@pytest.fixture(scope="module")
def reduced_motion_block(built_css: str) -> str:
    match = re.search(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\s*\)\s*\{(.+?\})\s*\}",
        built_css,
        re.DOTALL,
    )
    assert match, "hue's stylesheet does not answer prefers-reduced-motion at all"
    return match.group(1)


@pytest.mark.parametrize("declaration", REQUIRED)
def test_the_rule_shuts_motion_down(
    reduced_motion_block: str, declaration: str
) -> None:
    assert declaration in reduced_motion_block


def test_it_reaches_pseudo_elements_too(reduced_motion_block: str) -> None:
    # A spinner ring, a checkbox tick and a switch knob are all ::before.
    assert "::before" in reduced_motion_block or ":before" in reduced_motion_block
