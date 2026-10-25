"""
Code highlighted by Shiki, which is JavaScript, from Python.

Every block is highlighted once and kept in a cache keyed by its content, so a
render only reads a dictionary. A miss runs node for that block. A build
renders every page once in record mode first, which collects every miss, and
highlights them in a single node run, since each run pays for loading Shiki.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from html import escape
from pathlib import Path

_HERE = Path(__file__).parent
CACHE_PATH = _HERE.parents[2] / ".cache" / "highlight.json"

LANGUAGES = frozenset({"python", "bash", "css", "javascript", "html", "toml", "jsonc"})


class HighlightError(RuntimeError):
    pass


def _key(code: str, lang: str) -> str:
    return hashlib.sha256(f"{lang}\0{code}".encode()).hexdigest()


class Highlighter:
    def __init__(self, cache_path: Path = CACHE_PATH) -> None:
        self.cache_path = cache_path
        try:
            self.cache: dict[str, str] = json.loads(cache_path.read_text())
        except FileNotFoundError:
            self.cache = {}
        self._recording: dict[str, tuple[str, str]] | None = None

    def __call__(self, code: str, lang: str) -> str:
        if lang not in LANGUAGES:
            raise HighlightError(f"No highlighting set up for {lang!r}.")
        key = _key(code, lang)
        if key in self.cache:
            return self.cache[key]
        if self._recording is not None:
            self._recording[key] = (code, lang)
            return f'<pre class="shiki"><code>{escape(code)}</code></pre>'
        self.fill([(code, lang)])
        return self.cache[key]

    @contextmanager
    def record(self) -> Iterator[None]:
        """
        Collect what is missing instead of highlighting it, then highlight all
        of it in one go on the way out.
        """
        self._recording = {}
        try:
            yield
            self.fill(self._recording.values())
        finally:
            self._recording = None

    def fill(self, items: Iterable[tuple[str, str]]) -> None:
        batch = [{"code": code, "lang": lang} for code, lang in items]
        if not batch:
            return
        if not (_HERE / "node_modules").exists():
            raise HighlightError(
                "Shiki is not installed. Run `make highlight-deps` in hue-docs."
            )
        result = subprocess.run(
            ["node", str(_HERE / "highlight.mjs")],
            input=json.dumps(batch),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise HighlightError(result.stderr)
        for item, html in zip(batch, json.loads(result.stdout), strict=True):
            self.cache[_key(item["code"], item["lang"])] = html
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache))


highlight = Highlighter()
