"""
The code a reader sees for an example: the expression its function returns.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from functools import cache

from hue import ui

from hue_docs_v2.model import Example


class SnippetError(ValueError):
    pass


@cache
def snippet(example: Example) -> str:
    """
    The source of the one expression an example function returns.

    Raises when the function is anything else, because whatever else it did
    would be missing from the code shown beside what it rendered.
    """
    source = textwrap.dedent(inspect.getsource(example))
    function = ast.parse(source).body[0]
    if not isinstance(function, ast.FunctionDef):
        raise SnippetError(f"{example.__qualname__} is not a plain function.")

    body = function.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    ):
        body = body[1:]  # a docstring
    if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
        raise SnippetError(
            f"{example.__qualname__} must be a single return statement, so the "
            f"code shown is the code that rendered."
        )

    statement = body[0]
    segment = ast.get_source_segment(source, statement) or ""
    expr = segment.removeprefix("return").strip()
    # Continuation lines carry the function body's indentation.
    lines = expr.splitlines()
    indent = statement.col_offset
    lines[1:] = [
        line[indent:] if line[:indent].isspace() else line for line in lines[1:]
    ]
    # A multi-line chain keeps the parentheses it is wrapped in: without
    # them its line breaks would end the statement.
    return "\n".join(lines)


# Names an example uses that hue.ui does not export, and where they come from.
_ELSEWHERE = {
    "html": "from hue import html",
    "toast": "from hue import toast",
    "unsafe": "from hue.js import unsafe",
}

# The docs' own icon set stands in for the reader's, which they bind once.
_ICON = 'Icon = create_icon_base(icons_dir="path/to/icons")'


def imports(*snippets: str) -> str:
    """
    The lines that make the snippets run, from the names they use.
    """
    names: set[str] = set()
    for code in snippets:
        names |= {
            node.id for node in ast.walk(ast.parse(code)) if isinstance(node, ast.Name)
        }
    lines = [line for name, line in _ELSEWHERE.items() if name in names]
    from_ui = names & set(ui.__all__)
    if "Icon" in from_ui:
        from_ui = (from_ui - {"Icon"}) | {"create_icon_base"}
    if from_ui:
        lines.append(f"from hue.ui import {', '.join(sorted(from_ui))}")
    if "Icon" in names:
        lines += ["", _ICON]
    return "\n".join(lines)
