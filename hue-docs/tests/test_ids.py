"""
No id appears twice on a built page.

A docs page puts every variant, and every playground combination, into one
document at once - so a component that names its own id from a prop will
collide with its own copies. The markup stays valid and the page looks right;
it is the behaviour that breaks, because a label points at the first matching
id in the document rather than the one beside it. Clicking a card in the
playground then toggles a checkbox nobody can see.
"""

from __future__ import annotations

import collections
import re
from pathlib import Path

import pytest

DIST = Path(__file__).resolve().parent.parent / "dist"


def _pages() -> list[Path]:
    return sorted(DIST.rglob("*.html"))


@pytest.mark.skipif(not DIST.exists(), reason="site has not been built")
@pytest.mark.parametrize("page", _pages(), ids=lambda p: p.parent.name)
def test_no_id_appears_twice(page: Path) -> None:
    ids = re.findall(r'\sid="([^"]+)"', page.read_text())
    repeated = {name: n for name, n in collections.Counter(ids).items() if n > 1}

    assert not repeated, (
        f"{page.parent.name} repeats ids {sorted(repeated)}. Two controls on "
        f"one page cannot share a name: a label points at the first match in "
        f"the document, not the nearest one."
    )
