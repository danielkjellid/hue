from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Callout

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Icons"),
        pr.lead(
            "Hue does not ship an icon library — you bring your own. The Icon "
            "component inlines an SVG into the page so you can size and colour "
            "it with the same utility classes you use everywhere else."
        ),
        pr.p(
            "Because the icon source is pluggable, you are never locked into a "
            "particular set. Point Hue at a folder of SVGs, ship icons inside "
            "your Python package, or pull them from somewhere else entirely — "
            "the component does not care where the markup comes from."
        ),
        pr.h2("Bind an icon source"),
        pr.p(
            "Icons are not constructed directly. Call create_icon_base once to "
            "bind a source, then reuse the returned Icon class throughout your "
            "app. The common case is a directory of .svg files:"
        ),
        pr.code(
            "from hue.ui import create_icon_base\n\n"
            "Icon = create_icon_base(icons_dir=BASE_DIR / 'assets/icons')\n\n"
            "# elsewhere\n"
            'Icon("calendar")'
        ),
        pr.p(
            "The icon name is the filename without the .svg extension, so "
            "calendar resolves to calendar.svg in that directory. Files are "
            "read and parsed once per process and then cached, so rendering the "
            "same icon across hundreds of rows costs a single read."
        ),
        pr.h2("Size and colour"),
        pr.p(
            "The SVG is inlined, not referenced through an <img>, so utility "
            "classes apply directly. Size it with size-*, and colour it with "
            "text-* — provided the icon paints with currentColor (most icon "
            "sets do):"
        ),
        pr.code(
            'Icon("calendar").class_("size-4 text-primary")\n'
            'Icon("trash").class_("size-5 text-destructive")'
        ),
        pr.p(
            "Any width or height baked into the SVG file is stripped on render "
            "so it never fights your sizing classes — the viewBox alone drives "
            "the aspect ratio."
        ),
        pr.h2("What makes a good icon file"),
        pr.p(
            "Hue inlines the SVG verbatim, so every element an icon set uses — "
            "path, circle, rect, line, polyline, g, gradients — is preserved. "
            "Two things are required of each file:"
        ),
        pr.bullets(
            [
                pr.p("A single <svg> root element."),
                pr.p(
                    "A viewBox attribute, so the icon scales to whatever size "
                    "you give it."
                ),
            ]
        ),
        pr.p(
            "For icons that should inherit text colour, set fill or stroke to "
            "currentColor in the file rather than a fixed colour:"
        ),
        pr.code(
            '<svg viewBox="0 0 24 24">\n'
            '  <path d="M12 2v20" stroke="currentColor" stroke-width="2" />\n'
            "</svg>",
            language="html",
        ),
        pr.h2("Several sets at once"),
        pr.p(
            "Need outline and filled variants, or icons from two libraries? "
            "Bind one Icon class per source — each is independent:"
        ),
        pr.code(
            "OutlineIcon = create_icon_base(icons_dir=ICONS / 'outline')\n"
            "FilledIcon = create_icon_base(icons_dir=ICONS / 'filled')\n\n"
            'OutlineIcon("bell").class_("size-5")\n'
            'FilledIcon("bell").class_("size-5 text-primary")'
        ),
        pr.h2("Load icons from anywhere"),
        pr.p(
            "A directory is just the default. For full control — to ship icons "
            "inside a package, read from a sprite, or fetch them from a service "
            "— pass a resolver: any function that takes an icon name and returns "
            "SVG markup. This is the seam that keeps you from being locked in."
        ),
        pr.code(
            "from importlib.resources import files\n"
            "from hue.ui import create_icon_base\n\n"
            "def resolve(name: str) -> str:\n"
            '    return (files("my_app.icons") / f"{name}.svg").read_text()\n\n'
            "Icon = create_icon_base(resolver=resolve)"
        ),
        pr.p(
            "Shipping icons as package resources this way means they travel "
            "with your distribution and resolve correctly no matter where the "
            "app runs — no absolute paths to get wrong. Add your own caching "
            "inside the resolver if the source is slow to reach."
        ),
        Callout()
        .variant("warning")
        .title("Reading from disk? Build on directory_resolver")
        .content(
            "If your custom resolver just reads .svg files from a folder, wrap "
            "directory_resolver rather than opening files yourself. A hand-rolled "
            "reader re-reads and re-parses on every render and raises whatever "
            "error open() happens to throw — directory_resolver gives you the "
            "shared per-process cache and a consistent 'icon not found' message "
            "for free."
        ),
        pr.h2("icons_dir vs. directory_resolver"),
        pr.p(
            "These are not two different mechanisms — icons_dir is shorthand. "
            "directory_resolver(path) builds the resolver that reads .svg files "
            "from a folder, and passing icons_dir just calls it for you. The two "
            "lines below are exactly equivalent:"
        ),
        pr.code(
            "from hue.ui import create_icon_base, directory_resolver\n\n"
            'create_icon_base(icons_dir="assets/icons")\n'
            'create_icon_base(resolver=directory_resolver("assets/icons"))'
        ),
        pr.p(
            "So reach for icons_dir whenever you just want to read SVGs from a "
            "folder — that is the common case. Reach for directory_resolver only "
            "when you need the resolver as a value you can wrap or compose, such "
            "as falling back from one set to another:"
        ),
        pr.code(
            "from hue.ui import create_icon_base, directory_resolver\n\n"
            'project_icons = directory_resolver("assets/icons")\n'
            'vendor_icons = directory_resolver("assets/vendor")\n\n'
            "def resolve(name: str) -> str:\n"
            "    try:\n"
            "        return project_icons(name)\n"
            "    except RuntimeError:\n"
            "        return vendor_icons(name)  # fall back to the vendored set\n\n"
            "Icon = create_icon_base(resolver=resolve)"
        ),
        pr.h2("Accessibility"),
        pr.p(
            "Most icons are decorative — they sit beside a text label that "
            'already says what they mean. Hue marks icons aria-hidden="true" '
            "by default so screen readers skip them."
        ),
        pr.p(
            "When an icon is the only content of a control, give it an "
            "accessible name with .aria_label(). Doing so drops the decorative "
            "default automatically, so the label is announced:"
        ),
        pr.code(
            "from hue.ui import Button\n\n"
            'Button().class_("size-9").content(\n'
            '    Icon("trash").class_("size-5").aria_label("Delete")\n'
            ")"
        ),
    )


PAGE = ProsePage(
    slug="icons",
    title="Icons",
    nav_label="Icons",
    group="Guides",
    order=1,
    build=_build,
)
