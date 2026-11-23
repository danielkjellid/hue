"""
The docs as Markdown, for agents: one file per page and an llms.txt index.

Built from the same page declarations as the site, so the two cannot drift. A
component page is assembled from its model (lede, panels' code, props, notes),
and only the hand-written parts, a page's usage and a guide's body, go through
HTML: they are trees of hue components, rendered and then read back.

Links are relative, so the same files work on the site and inside the hue-ui
wheel, where make dist puts them.
"""

from __future__ import annotations

import asyncio
import posixpath
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from importlib.metadata import version
from pathlib import Path

from hue.types.core import ComponentType
from hue.ui.base import ChainableComponent

from hue_docs.highlight import highlight
from hue_docs.layout.panel import panel_code
from hue_docs.model import ComponentPage, GuidePage
from hue_docs.nav import build_nav
from hue_docs.pages import COMPONENTS, GUIDES
from hue_docs.props import props_of
from hue_docs.render import render_html

SUMMARY = (
    "Hue is a component library for Python that renders HTML. Components are "
    "chainable Python objects rendered with htmy, styled with Tailwind and made "
    "interactive with Alpine.js and Alpine AJAX. hue-django and hue-fastapi "
    "integrate it with those frameworks."
)

# Controls and decoration, which have no Markdown and say nothing to a reader.
_SKIP = {"button", "iframe", "svg", "template", "script", "style", "input", "select"}
_BLOCK = {
    "p", "pre", "ul", "ol", "table", "div", "section", "header", "main",
    "article", "aside", "nav", "footer", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6",
}  # fmt: skip
_EMPHASIS = {"strong": "**{}**", "b": "**{}**", "em": "*{}*", "i": "*{}*"}
_VOID = {"br", "hr", "img", "input", "meta", "link", "source", "col", "wbr"}


def md_path(href: str) -> str:
    """
    / becomes index.md and /components/button/ components/button.md.
    """
    path = href.strip("/")
    return f"{path or 'index'}.md"


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[_Node | str] = field(default_factory=list)


class _Tree(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, {k: v or "" for k, v in attrs})
        self._stack[-1].children.append(node)
        if tag not in _VOID:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def _skipped(node: _Node) -> bool:
    return (
        node.tag in _SKIP
        or node.attrs.get("aria-hidden") == "true"
        or node.attrs.get("role") == "separator"
        or "sr-only" in node.attrs.get("class", "").split()
    )


def _text(node: _Node | str) -> str:
    if isinstance(node, str):
        return node
    return "".join(_text(child) for child in node.children)


class _Writer:
    def __init__(self, here: str) -> None:
        # The page's own path, which relative links are worked out from.
        self.here = posixpath.dirname(here)

    def _href(self, href: str) -> str:
        if not href.startswith("/") or href.startswith("//"):
            return href
        path, _, anchor = href.partition("#")
        target = posixpath.relpath(md_path(path), self.here or ".")
        return f"{target}#{anchor}" if anchor else target

    def inline(self, node: _Node | str) -> str:
        if isinstance(node, str):
            return re.sub(r"\s+", " ", node)
        if _skipped(node):
            return ""
        if node.tag == "code":
            return f"`{_text(node)}`"
        if node.tag == "br":
            return "\n"
        inner = "".join(self.inline(child) for child in node.children)
        if node.tag == "a":
            return f"[{inner.strip()}]({self._href(node.attrs.get('href', ''))})"
        wrap = _EMPHASIS.get(node.tag)
        return wrap.format(inner.strip()) if wrap else inner

    def blocks(self, node: _Node) -> list[str]:
        out: list[str] = []
        run: list[str] = []

        def flush() -> None:
            text = "".join(run).strip()
            if text:
                out.append(text)
            run.clear()

        for child in node.children:
            if isinstance(child, _Node) and child.tag in _BLOCK and not _skipped(child):
                flush()
                out.extend(self.block(child))
            else:
                run.append(self.inline(child))
        flush()
        return out

    def block(self, node: _Node) -> list[str]:
        tag = node.tag
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            return [f"{'#' * int(tag[1])} {self.inline(node).strip()}"]
        if tag == "pre":
            language = node.attrs.get("data-language", "")
            return [f"```{language}\n{_text(node).strip(chr(10))}\n```"]
        if tag in {"ul", "ol"}:
            return [self._list(node)]
        if tag == "table":
            return [self._table(node)]
        return self.blocks(node)

    def _list(self, node: _Node) -> str:
        lines = []
        items = [c for c in node.children if isinstance(c, _Node) and c.tag == "li"]
        for number, item in enumerate(items, start=1):
            marker = f"{number}." if node.tag == "ol" else "-"
            body = "\n\n".join(self.blocks(item))
            pad = " " * (len(marker) + 1)
            first, *rest = body.splitlines() or [""]
            lines.append(f"{marker} {first}")
            lines.extend(f"{pad}{line}" if line else "" for line in rest)
        return "\n".join(lines)

    def _table(self, node: _Node) -> str:
        rows: list[list[str]] = []

        def walk(each: _Node) -> None:
            for child in each.children:
                if not isinstance(child, _Node):
                    continue
                if child.tag == "tr":
                    rows.append(
                        [
                            self.inline(cell).strip().replace("|", "\\|")
                            for cell in child.children
                            if isinstance(cell, _Node) and cell.tag in {"th", "td"}
                        ]
                    )
                else:
                    walk(child)

        walk(node)
        if not rows:
            return ""
        return _table(rows[0], rows[1:])


def _table(head: list[str], body: list[list[str]]) -> str:
    lines = [f"| {' | '.join(head)} |", f"|{'---|' * len(head)}"]
    lines += [f"| {' | '.join(row)} |" for row in body]
    return "\n".join(lines)


def html_to_markdown(html: str, *, here: str = "index.md") -> str:
    tree = _Tree()
    tree.feed(html)
    return "\n\n".join(_Writer(here).blocks(tree.root))


async def _render(tree: ComponentType, here: str) -> str:
    return html_to_markdown(await render_html(tree, request=object()), here=here)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _props(cls: type[ChainableComponent]) -> str:
    props = props_of(cls)
    if not props:
        return f"{cls.__name__} has no modifiers of its own."
    return _table(
        ["Modifier", "Default", "Description"],
        [
            [f"`{_cell(p.signature)}`", _cell(p.default or "-"), _cell(p.doc or "-")]
            for p in props
        ],
    )


async def component_markdown(page: ComponentPage) -> str:
    here = md_path(page.href)
    names = ", ".join([page.title, *[part.__name__ for part in page.parts]])
    out = [
        f"# {page.title}",
        page.lede,
        f"```python\n{page.import_line or f'from hue.ui import {names}'}\n```",
    ]
    if page.panels:
        out.append("## Examples")
        for panel in page.panels:
            out.append(f"### {panel.label}")
            if panel.hint:
                out.append(panel.hint)
            out.append(f"```python\n{panel_code(panel)}\n```")
    if page.usage is not None:
        out.append(await _render(page.usage(), here))
    out += ["## API", _props(page.component)]
    for part in page.parts:
        out += [f"### {part.__name__}", _props(part)]
    if page.notes:
        labels = {"a11y": "Accessibility", "note": "Note", "warn": "Watch"}
        out.append("## Notes")
        out.append("\n".join(f"- **{labels[n.kind]}:** {n.text}" for n in page.notes))
    by_class = {other.component: other for other in COMPONENTS}
    related = [by_class[cls] for cls in page.related if cls in by_class]
    if related:
        out.append("## Related")
        folder = posixpath.dirname(here)
        out.append(
            "\n".join(
                f"- [{o.title}]({posixpath.relpath(md_path(o.href), folder)})"
                for o in related
            )
        )
    return "\n\n".join(out) + "\n"


async def guide_markdown(page: GuidePage) -> str:
    return await _render(page.build(), md_path(page.href)) + "\n"


def llms_txt() -> str:
    ledes = {page.href: page.lede for page in COMPONENTS}
    out = [f"# Hue {version('hue-ui')}", f"> {SUMMARY}"]
    for group in build_nav(GUIDES, COMPONENTS):
        out.append(f"## {group.title}")
        lines = []
        for item in group.items:
            line = f"- [{item.label}]({md_path(item.href)})"
            lede = ledes.get(item.href)
            if lede:
                line += f": {lede.split('. ')[0].rstrip('.')}."
            lines.append(line)
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


async def _pages() -> dict[str, str]:
    files = {md_path(page.href): await guide_markdown(page) for page in GUIDES}
    for page in COMPONENTS:
        files[md_path(page.href)] = await component_markdown(page)
    return files


def write_markdown(out: Path) -> None:
    # Plain blocks: highlighting runs while the trees are built, so the whole
    # build goes inside, and Markdown has no use for Shiki's markup anyway.
    with highlight.plain():
        files = asyncio.run(_pages())
    files["llms.txt"] = llms_txt()
    for path, text in files.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)


if __name__ == "__main__":
    write_markdown(Path(sys.argv[1]))
