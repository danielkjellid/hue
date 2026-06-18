"""Build-time syntax highlighting with Pygments.

Highlighting happens at build time and is embedded as plain HTML spans, so the
site stays fully static — no client-side highlighter, no CDN. A light theme is
emitted under ``.highlight`` and a dark one under ``[data-theme=dark]
.highlight`` to match Hue's theme toggle.
"""

from __future__ import annotations

from functools import lru_cache

from htmy import SafeStr
from pygments import highlight as _highlight
from pygments.formatters import HtmlFormatter
from pygments.lexer import Lexer
from pygments.lexers import BashLexer, PythonLexer

# nowrap=True emits just the token spans (no wrapping <div>/<pre>) so we can
# place them inside our own styled <pre><code>.
_FORMATTER = HtmlFormatter(nowrap=True)

_LEXERS: dict[str, Lexer] = {
    "python": PythonLexer(),
    "bash": BashLexer(),
}


def highlight_code(source: str, language: str = "python") -> SafeStr:
    lexer = _LEXERS.get(language, _LEXERS["python"])
    return SafeStr(_highlight(source, lexer, _FORMATTER).rstrip("\n"))


@lru_cache(maxsize=1)
def highlight_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs("[data-theme=dark] .highlight")
    return f"{light}\n{dark}\n"
