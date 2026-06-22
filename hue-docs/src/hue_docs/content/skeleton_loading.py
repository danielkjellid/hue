from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Skeleton loading"),
        pr.lead(
            "Show a placeholder shaped like your content while it loads. Because "
            "a hue page is a tree of Python components, the skeleton is derived "
            "from that tree rather than measured from a rendered screen."
        ),
        pr.p(
            "There are three pieces: the Skeleton atom (the pulsing shapes), "
            "to_skeleton (maps a component tree to a skeleton of itself), and "
            "defer (renders the skeleton now and fetches the real content into "
            "its place)."
        ),
        pr.h2("The Skeleton atom"),
        pr.p(
            "Skeleton renders a single pulsing placeholder. Pick a shape, a line "
            "for text, a circle for avatars, a rect for images and cards, and "
            "optionally override its width, height, or corners with Tailwind "
            "classes. lines() renders a stacked paragraph whose last line is "
            "shortened. The pulse respects prefers-reduced-motion, and the shape "
            "is always marked aria-hidden because it is decorative."
        ),
        pr.code(
            "from hue.ui import Skeleton\n\n"
            'Skeleton().shape("circle").height("size-8")\n'
            'Skeleton().shape("rect").height("h-40")\n'
            "Skeleton().lines(3)"
        ),
        pr.p(pr.link("See the Skeleton component page", "/components/skeleton/")),
        pr.h2("Mapping a tree with to_skeleton"),
        pr.p(
            "to_skeleton walks a component tree and returns a skeleton of it. "
            "Each component contributes its own placeholder, a button becomes a "
            "rect its size, text becomes a line, and layout containers (Stack, "
            "html.div, ...) keep their classes and have their children mapped in "
            "place. So the skeleton keeps the real layout and only the leaves "
            "turn into shapes. Anything it doesn't recognise degrades to a line."
        ),
        pr.code(
            "from hue.skeletonize import to_skeleton\n"
            "from hue.ui import Stack, Text, Button\n\n"
            "layout = Stack().content(\n"
            '    Text("Dashboard").variant("title-1"),\n'
            '    Button().variant("primary").content("Export"),\n'
            ")\n\n"
            "skeleton = to_skeleton(layout)"
        ),
        pr.p(
            "Components set their own default via _skeleton_impl. The defaults "
            "are deliberately simple, they track props like a button's size or a "
            "heading's scale, but they can't know your data."
        ),
        pr.h2("Overriding the default"),
        pr.p(
            "For dynamic content, a comment body that wraps to three lines, a "
            "list whose length you only know at runtime, the per-class guess is "
            "the wrong shape. skeleton_as overrides the placeholder for a single "
            "instance, and it wins over the class default and over container "
            "recursion. Pass a component, or a zero-arg factory to defer building "
            "it."
        ),
        pr.code(
            "from hue.ui import Skeleton, Text\n\n"
            "# This text loads as three lines, not one.\n"
            "Text(comment.body).skeleton_as(Skeleton().lines(3))\n\n"
            "# A factory defers construction until the skeleton is built.\n"
            "Stack().content(*rows).skeleton_as(\n"
            "    lambda: Stack().content(*[Skeleton().lines(2) for _ in range(5)])\n"
            ")"
        ),
        pr.h2("Deferring content"),
        pr.p(
            "defer renders a skeleton immediately and, on init, fetches the real "
            "content with Alpine AJAX and merges it into the same target. The "
            "skeleton is built from the data-free shape of the content, so it "
            "never blocks on the I/O you are trying to defer. Point a fragment "
            "route at the url and return the content wrapped in the target."
        ),
        pr.code(
            "from hue_django.skeletonize import defer\n"
            "from hue.router import HueResponse\n\n"
            "class DashboardView(HueView):\n"
            "    router = Router[HttpRequest]()\n\n"
            "    async def index(self, request, context):\n"
            "        return Page(\n"
            '            title="Dashboard",\n'
            "            body=defer(\n"
            "                layout=dashboard_content,\n"
            '                url="/dashboard/content/",\n'
            '                target="dashboard-body",\n'
            "            ),\n"
            "        )\n\n"
            '    @router.fragment_get("content/")\n'
            "    async def content(self, request, context):\n"
            "        data = await load_dashboard()  # the slow part\n"
            "        return HueResponse(\n"
            '            component=dashboard_content(data), target="dashboard-body"\n'
            "        )"
        ),
        pr.p(
            "Skeleton generation must stay data-free. Under DEBUG, the Django "
            "defer builds the skeleton inside a guard that raises if it touches "
            "the database, so a layout that accidentally loads data (for example "
            "by sizing a list from len(queryset)) fails loudly instead of "
            "quietly re-introducing the I/O you meant to defer."
        ),
    )


PAGE = ProsePage(
    slug="skeleton-loading",
    title="Skeleton loading",
    nav_label="Skeleton loading",
    group="Guides",
    order=2,
    build=_build,
)
