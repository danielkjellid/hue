"""
Curated showcases for the TableOfContents molecule.

There is nothing to toggle and nothing to pass it but where to read, so what
the examples have to show is that it reads: one has an article of its own
beside it, the other is reading this page.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_PARAGRAPH = (
    "Nothing here is passed to the table of contents. It found this heading "
    "by reading the article beside it."
)

# h4 and h5 rather than h2 and h3, so this little article's headings stay out
# of the specimen below that is reading the whole page.
_ARTICLE = ", ".join(
    f'html.{tag}("{label}", class_="{classes}"), html.p(_TEXT, class_="_BODY")'
    for tag, label, classes in [
        ("h4", "Introduction", "font-ui text-lg font-bold"),
        ("h4", "Core concepts", "font-ui text-lg font-bold"),
        ("h5", "Architecture", "font-ui text-base font-bold"),
        ("h5", "Data flow", "font-ui text-base font-bold"),
        ("h4", "Components", "font-ui text-lg font-bold"),
        ("h4", "Deployment", "font-ui text-lg font-bold"),
    ]
)
_ARTICLE = _ARTICLE.replace("_TEXT", f'"{_PARAGRAPH}"').replace(
    '"_BODY"', '"mb-6 text-sm text-fg-muted"'
)

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Point it at the element holding the content and it reads the "
            "headings out of it, nesting them by their own levels and "
            "drawing the rail from where the rows landed. There is no list "
            "to pass and none to keep in step: a heading without an id is "
            "given one from its own words - or linked through the section "
            "around it, where that already has one - and content swapped in "
            "by a fragment rebuilds the entries rather than leaving them "
            'stale. aria-current is "location" rather than "page": every '
            "entry points at the page you are already on, and what is marked "
            "is where in it you have got to."
        ),
        variants=[
            variant(
                "An article of its own",
                "html.div("
                f"html.article({_ARTICLE}, id='toc-article', class_='min-w-0 flex-1'), "
                # The width goes on a wrapper: the nav is w-full, so it
                # fills whatever column it is given rather than arguing
                # with it.
                "html.div(TableOfContents().of('#toc-article', "
                "headings='h4, h5'), class_='w-56 flex-none'), "
                "class_='flex w-full gap-10')",
            ),
            variant(
                "This page, under another name",
                'TableOfContents().of("main").title("Contents")'
                '.class_("max-w-60")',
            ),
        ],
    ),
]
