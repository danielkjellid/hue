"""
What the guides tell a reader to type, checked against hue itself.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

from hue.assets import css_source_path

GUIDES = (
    Path(__file__).resolve().parents[2] / "src" / "hue_docs_v2" / "pages" / "guides"
)


def _code_blocks() -> list[tuple[str, str]]:
    """
    Every string a guide passes to pr.code, with where it came from. A name
    is looked up in its module, as the guides keep longer blocks in one.
    """
    found = []
    for path in sorted(GUIDES.glob("*.py")):
        module = importlib.import_module(f"hue_docs_v2.pages.guides.{path.stem}")
        for node in ast.walk(ast.parse(path.read_text())):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "code"
                and node.args
            ):
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Name):
                source = getattr(module, arg.id)
            elif isinstance(arg, ast.Constant):
                source = arg.value
            else:
                continue
            found.append((f"{path.name}:{node.lineno}", source))
    return found


def test_every_css_property_a_guide_names_is_one_hue_defines() -> None:
    # The LEGACY block keeps old names alive for unmigrated components; a
    # reader who overrides one of them changes nothing anyone sees.
    theme = css_source_path().read_text().split("LEGACY", 1)[0]
    defined = set(re.findall(r"(--[\w-]+)\s*:", theme))
    blocks = _code_blocks()
    assert blocks
    unknown = [
        f"{where} {name}"
        for where, source in blocks
        for name in re.findall(r"(--[a-z][\w-]*)\s*:", source)
        if name not in defined
    ]
    assert not unknown, unknown
