"""
Curated showcases for the TableOfContents molecule.

There is nothing to toggle and nothing to pass it but where to read, so what
the examples have to show is that it reads - and that it keeps up. The first
is an article long enough to scroll inside its own panel.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_ARTICLE = """
                    html.h4("Introduction", class_=HEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h4("Core concepts", class_=HEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h5("Architecture", class_=SUBHEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h5("Data flow", class_=SUBHEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h4("Components", class_=HEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h5("Buttons", class_=SUBHEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h5("Forms", class_=SUBHEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.p(BODY, class_=PARAGRAPH),
                    html.h4("Deployment", class_=HEADING),
                    html.p(BODY, class_=PARAGRAPH),
                    html.p(BODY, class_=PARAGRAPH),
"""

# The names the snippet above leans on, so the code reads as prose rather
# than as the same class list written out twenty times.
_NS = {
    "HEADING": "mt-8 font-ui text-lg font-bold first:mt-0",
    "SUBHEADING": "mt-6 font-ui text-base font-bold",
    "PARAGRAPH": "mt-2 text-sm leading-[1.7] text-fg-muted",
    "BODY": (
        "Nothing on this page is passed to the table of contents beside it. "
        "It found this section by reading the article, worked out how deep "
        "it sits from the heading level, and drew the rail from where the "
        "rows landed. Scroll the panel and the fill follows you down it."
    ),
}

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Point it at the element holding the content and it reads the "
            "headings out of it, nesting them by their own levels and "
            "drawing the rail from where the rows landed. Everything it "
            "measures is taken from whatever the content scrolls inside, so "
            "a contents beside a panel works the same way as one beside a "
            "page. There is no list to pass and none to keep in step: a "
            "heading without an id is given one from its own words - or "
            "linked through the section around it, where that already has "
            "one - and content swapped in by a fragment rebuilds the "
            "entries rather than leaving them stale."
        ),
        variants=[
            variant(
                "An article of its own, scrolling",
                """
                html.div(
                    html.article(
%s                        id="toc-article",
                        class_="h-80 min-w-0 flex-1 overflow-y-auto rounded-lg "
                        "border border-border bg-canvas-subtle px-5 py-4",
                    ),
                    html.div(
                        TableOfContents()
                            .of("#toc-article", headings="h4, h5")
                            .label("Documentation"),
                        class_="w-56 flex-none",
                    ),
                    class_="flex w-full gap-10",
                )
                """
                % _ARTICLE.lstrip("\n"),
                _NS,
            ),
        ],
    ),
]
