"""Build-time syntax highlighting with Pygments.

Highlighting happens at build time and is embedded as plain HTML spans, so the
site stays fully static — no client-side highlighter, no CDN. A light theme is
emitted under ``.highlight`` and a dark one under ``[data-theme=dark]
.highlight`` to match Hue's theme toggle.

Pygments' lexers leave a lot on the table for our code samples: its Python
lexer tags every identifier as a generic ``Name`` (so class instantiations and
method calls render black in the default theme), and its Bash lexer tags
command words as plain ``Text`` (so shell snippets look unhighlighted). The
filters below promote those generic tokens to richer types the theme already
colors.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from functools import lru_cache
from typing import ClassVar

from htmy import SafeStr
from pygments import highlight as _highlight
from pygments.filter import Filter
from pygments.formatters import HtmlFormatter
from pygments.lexer import Lexer
from pygments.lexers import BashLexer, CssLexer, PythonLexer
from pygments.token import Name, Text, Token, _TokenType

# A single token in Pygments' stream: its type and its text.
Token_ = tuple[_TokenType, str]

# nowrap=True emits just the token spans (no wrapping <div>/<pre>) so we can
# place them inside our own styled <pre><code>.
_FORMATTER = HtmlFormatter(nowrap=True)


def _next_significant(tokens: list[Token_], start: int) -> str | None:
    """Return the value of the next non-whitespace token after ``start``."""
    for ttype, value in tokens[start:]:
        if ttype in Token.Text.Whitespace or not value.strip():
            continue
        return value
    return None


class _PythonNamesFilter(Filter):
    """Resolve generic Python ``Name`` tokens into class/call/kwarg tokens.

    Pygments can't tell ``Button(...)`` (a class instantiation) or ``.variant()``
    (a method call) from any other identifier — all are ``Name``. We apply
    editor-style heuristics: TitleCase names are classes, names followed by
    ``(`` are calls, and names followed by ``=`` (inside a call) are keyword
    arguments.
    """

    def filter(self, lexer: Lexer, stream: Iterable[Token_]) -> Iterator[Token_]:
        tokens = list(stream)
        depth = 0
        for i, (ttype, value) in enumerate(tokens):
            if ttype is Name:
                nxt = _next_significant(tokens, i + 1)
                if value[:1].isupper():
                    yield Name.Class, value
                elif nxt == "(":
                    yield Name.Function, value
                elif nxt == "=" and depth > 0:
                    # A name followed by ``=`` is a keyword argument only inside
                    # a call; at the top level it's an assignment target.
                    yield Name.Attribute, value
                else:
                    yield ttype, value
                continue
            if value == "(":
                depth += 1
            elif value == ")":
                depth = max(0, depth - 1)
            yield ttype, value


class _BashCommandFilter(Filter):
    """Tag the leading word of each shell command as ``Name.Function``.

    Bash command words arrive as plain ``Text`` (no span). We mark the first
    word of every command — at the start of input or after a separator like
    ``|``, ``;``, ``&&`` or a newline — so commands stand out.
    """

    _SEPARATORS: ClassVar[set[str]] = {"|", ";", "&", "&&", "||", "\n", "(", "{"}

    def filter(self, lexer: Lexer, stream: Iterable[Token_]) -> Iterator[Token_]:
        at_command_start = True
        for ttype, value in stream:
            if ttype in Token.Text.Whitespace:
                if "\n" in value:
                    at_command_start = True
                yield ttype, value
                continue
            if at_command_start and ttype in Text and value.strip():
                yield Name.Function, value
                at_command_start = False
                continue
            at_command_start = value.strip() in self._SEPARATORS
            yield ttype, value


def _python_lexer() -> Lexer:
    lexer = PythonLexer()
    lexer.add_filter(_PythonNamesFilter())
    return lexer


def _bash_lexer() -> Lexer:
    lexer = BashLexer()
    lexer.add_filter(_BashCommandFilter())
    return lexer


_LEXERS: dict[str, Lexer] = {
    "python": _python_lexer(),
    "bash": _bash_lexer(),
    "css": CssLexer(),
}


def highlight_code(source: str, language: str = "python") -> SafeStr:
    lexer = _LEXERS.get(language, _LEXERS["python"])
    return SafeStr(_highlight(source, lexer, _FORMATTER).rstrip("\n"))


@lru_cache(maxsize=1)
def highlight_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs("[data-theme=dark] .highlight")
    return f"{light}\n{dark}\n"
