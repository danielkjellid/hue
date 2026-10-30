"""
The code blocks in the prose run as written, as far as code shown on its own
can: every one parses, and a component page's snippets run against hue.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest
from hue import html, ui

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout.panel import panel_code
from hue_docs_v2.pages import COMPONENTS

PAGES = Path(__file__).resolve().parents[2] / "src" / "hue_docs_v2" / "pages"


def _python_blocks() -> list[tuple[str, str]]:
    """
    Every Python pr.code() in pages/, read from the source: a string, a
    module constant, or an f-string, whose fields are taken to be a name.
    """
    blocks = []
    for path in sorted(PAGES.rglob("*.py")):
        parts = path.relative_to(PAGES).with_suffix("").parts
        module = importlib.import_module("hue_docs_v2.pages." + ".".join(parts))
        for node in ast.walk(ast.parse(path.read_text())):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "code"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "pr"
            ):
                continue
            language = next(
                (k.value for k in node.keywords if k.arg == "language"), None
            )
            if isinstance(language, ast.Constant) and language.value != "python":
                continue
            source = node.args[0]
            if isinstance(source, ast.Name):
                code = getattr(module, source.id)
            elif isinstance(source, ast.JoinedStr):
                code = "".join(
                    part.value if isinstance(part, ast.Constant) else "Name"
                    for part in source.values
                )
            else:
                code = ast.literal_eval(source)
            blocks.append((f"{path.relative_to(PAGES)}:{node.lineno}", code))
    return blocks


BLOCKS = _python_blocks()


@pytest.mark.parametrize("where,code", BLOCKS, ids=[where for where, _ in BLOCKS])
def test_a_python_block_parses(where: str, code: str) -> None:
    # As the body of an async function, since a snippet can be a handler's
    # lines: an await, or a return.
    body = "\n".join(f"    {line}" for line in code.splitlines())
    compile(f"async def snippet():\n{body}\n    pass", where, "exec")


HUE = {name: getattr(ui, name) for name in ui.__all__} | {"html": html, "Icon": Icon}


@pytest.mark.parametrize(
    "where,code",
    [(where, code) for where, code in BLOCKS if where.startswith("components/")],
    ids=[where for where, _ in BLOCKS if where.startswith("components/")],
)
def test_a_component_snippet_runs_against_hue(where: str, code: str) -> None:
    """
    A wrong modifier or argument raises. A name hue does not export is the
    reader's own, such as their rows or their request, and is let through.
    """
    compiled = compile(code, where, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    try:
        exec(compiled, dict(HUE))
    except NameError as error:
        assert error.name not in HUE, error


@pytest.mark.parametrize("page", COMPONENTS, ids=[page.slug for page in COMPONENTS])
def test_no_panel_code_loads_itself_from_a_docs_route(page) -> None:
    # A specimen that fetches its content from /demos/ shows the reader a
    # loader instead of the code that draws it, so its panel shows the view.
    for panel in page.panels:
        code = panel_code(panel)
        assert not ("x_init(" in code and "/demos/" in code), panel.slug
