from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Avatar, Button
from hue.ui import Icon as HueIconClass

from hue_docs.icons import Icon
from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def bell() -> ComponentType:
    return Icon("bell").class_("size-6")


# Sizes


def size_4() -> ComponentType:
    return Icon("calendar").class_("size-4")


def size_5() -> ComponentType:
    return Icon("calendar").class_("size-5")


def size_6() -> ComponentType:
    return Icon("calendar").class_("size-6")


def size_8() -> ComponentType:
    return Icon("calendar").class_("size-8")


def size_12() -> ComponentType:
    return Icon("calendar").class_("size-12")


# Colour


def inherited() -> ComponentType:
    return Icon("heart").class_("size-6")


def muted() -> ComponentType:
    return Icon("heart").class_("size-6 text-fg-subtle")


def accent() -> ComponentType:
    return Icon("heart").class_("size-6 text-accent-text")


def danger() -> ComponentType:
    return Icon("heart").class_("size-6 text-danger-text")


# Glyphs


def check() -> ComponentType:
    return Icon("check").class_("size-6")


def plus() -> ComponentType:
    return Icon("plus").class_("size-6")


def arrow_right() -> ComponentType:
    return Icon("arrow-right").class_("size-6")


def trash() -> ComponentType:
    return Icon("trash").class_("size-6")


def star() -> ComponentType:
    return Icon("star").class_("size-6")


def calendar() -> ComponentType:
    return Icon("calendar").class_("size-6")


# Accessible name


def decorative() -> ComponentType:
    return Icon("star").class_("size-6")


def labelled() -> ComponentType:
    return Icon("star").class_("size-6").role("img").aria_label("Starred")


def in_an_icon_button() -> Button:
    return Button().variant("outline").icon_only("Delete").content(Icon("trash"))


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Bind an icon source"),
        pr.p(
            "Hue ships no icon set for your own use, so an `Icon` draws from a "
            "source you bind. Call `create_icon_base` once with a folder of `.svg` "
            "files and use the class it returns everywhere. The `Icon` in `hue.ui` "
            "has no source of its own: rendering one with a name raises an "
            "error that says to call `create_icon_base`."
        ),
        pr.code(
            "from hue.ui import create_icon_base\n\n"
            'Icon = create_icon_base(icons_dir=BASE_DIR / "assets/icons")\n\n'
            "# elsewhere\n"
            'Icon("calendar")'
        ),
        pr.p(
            'The name is the file name without `.svg`, so `"calendar"` reads '
            "`calendar.svg` from that folder. An `Icon` with an empty name renders "
            "nothing. Each file is read and parsed once per process and then "
            "cached, so the same `Icon` in a hundred table rows costs one read."
        ),
        pr.h2("Size and colour an Icon"),
        pr.p(
            "An `Icon` inlines the SVG into the page instead of pointing an `img` "
            "at it, so utility classes reach it. Size it with `size-*`. Colour it "
            "with `text-*`, which works when the SVG paints with `currentColor`, as "
            "most icon sets do."
        ),
        pr.code(
            'Icon("calendar").class_("size-4 text-accent-text")\n'
            'Icon("trash").class_("size-5 text-danger-text")'
        ),
        pr.p(
            "The `Icon` drops any `width` and `height` set on the file's `svg` "
            "element, so they never fight your size classes, and the `viewBox` "
            "alone sets the aspect ratio. A class already in the file is kept, and the "
            "classes from `class_()` are added after it."
        ),
        pr.h2("What an Icon file needs"),
        pr.p(
            "An `Icon` inlines everything inside the `svg` element as it is, so any "
            "element an icon set uses (`path`, `circle`, `rect`, `line`, `polyline`, "
            "`g`, gradients) survives. Each file needs two things, and an `Icon` "
            "raises an error when either is missing:"
        ),
        pr.bullets(
            [
                pr.p("A single `svg` root element."),
                pr.p("A `viewBox`, so the icon scales to whatever size you give it."),
            ]
        ),
        pr.p(
            "For an icon that takes the text colour, set `fill` or `stroke` to "
            "`currentColor` in the file instead of a fixed colour:"
        ),
        pr.code(
            '<svg viewBox="0 0 24 24">\n'
            '  <path d="M12 2v20" stroke="currentColor" stroke-width="2" />\n'
            "</svg>",
            language="html",
        ),
        pr.h2("Use several icon sets at once"),
        pr.p(
            "Each call to `create_icon_base` returns its own `Icon` class with its "
            "own source, so outline and filled sets, or two libraries, live "
            "side by side:"
        ),
        pr.code(
            'OutlineIcon = create_icon_base(icons_dir=ICONS / "outline")\n'
            'FilledIcon = create_icon_base(icons_dir=ICONS / "filled")\n\n'
            'OutlineIcon("bell").class_("size-5")\n'
            'FilledIcon("bell").class_("size-5 text-accent-text")'
        ),
        pr.h2("Load Icon markup from anywhere"),
        pr.p(
            "A folder is only the default. Pass `create_icon_base` a `resolver` "
            "instead: any function that takes an icon name and returns SVG "
            "markup. It can read icons shipped inside your Python package, a "
            "sprite or a service. Icons shipped as package resources travel "
            "with your distribution, so no absolute path can go wrong where "
            "the app runs."
        ),
        pr.code(
            "from importlib.resources import files\n"
            "from hue.ui import create_icon_base\n\n"
            "def resolve(name: str) -> str:\n"
            '    return (files("my_app.icons") / f"{name}.svg").read_text()\n\n'
            "Icon = create_icon_base(resolver=resolve)"
        ),
        pr.p(
            "An `Icon` calls its resolver on every render and caches the parse "
            "of the markup it gets back. Caching the fetch itself is up to the "
            "resolver, so add a cache inside one whose source is slow to reach."
        ),
        pr.h3("icons_dir is directory_resolver"),
        pr.p(
            "`icons_dir` is shorthand. `directory_resolver(path)` builds the "
            "resolver that reads `.svg` files from a folder, and `icons_dir` calls "
            "it for you. These two lines do the same thing:"
        ),
        pr.code(
            "from hue.ui import create_icon_base, directory_resolver\n\n"
            'create_icon_base(icons_dir="assets/icons")\n'
            'create_icon_base(resolver=directory_resolver("assets/icons"))'
        ),
        pr.p(
            "Use `icons_dir` to read a folder. Use `directory_resolver` when you "
            "need the resolver as a value to wrap, such as falling back from "
            "one set to another. `directory_resolver` raises a `RuntimeError` for "
            "a name with no file, which is what the fallback catches:"
        ),
        pr.code(
            "from hue.ui import create_icon_base, directory_resolver\n\n"
            'project_icons = directory_resolver("assets/icons")\n'
            'vendor_icons = directory_resolver("assets/vendor")\n\n'
            "def resolve(name: str) -> str:\n"
            "    try:\n"
            "        return project_icons(name)\n"
            "    except RuntimeError:\n"
            "        return vendor_icons(name)\n\n"
            "Icon = create_icon_base(resolver=resolve)"
        ),
        pr.p(
            "A resolver that reads `.svg` files from a folder should wrap "
            "`directory_resolver` instead of opening files itself. "
            "`directory_resolver` reads each file once per process, raises one "
            "consistent error for a missing icon, and refuses a name that "
            "points outside its folder."
        ),
        pr.h2("Icon accessibility"),
        pr.p(
            'An `Icon` renders `aria-hidden="true"` by default, because most icons '
            "sit beside a label that already says what they mean. Setting "
            "`aria_label()`, `role()` or `aria_hidden()` on the `Icon` drops that "
            "default."
        ),
        pr.p(
            "An `Icon` that carries meaning on its own takes a name. Give it "
            '`role("img")` and `aria_label()`, so it is announced as an image '
            "with that name:"
        ),
        pr.code('Icon("star").class_("size-5").role("img").aria_label("Starred")'),
        pr.p(
            "In a button that holds only an icon, name the button instead. "
            "`Button.icon_only()` takes the name as its argument, and the `Icon` "
            "inside stays hidden:"
        ),
        pr.code('Button().icon_only("Delete").content(Icon("trash"))'),
    )


PAGE = ComponentPage(
    HueIconClass,
    import_line="from hue.ui import create_icon_base",
    lede=(
        "An icon draws an SVG inline, from an icon set you bind once with "
        "`create_icon_base`. Size and colour it with the same utility classes "
        "as everything else on the page."
    ),
    usage=_usage,
    panels=[
        panel("Live", bell, layout="center"),
        panel(
            "Sizes",
            size_4,
            size_5,
            size_6,
            size_8,
            size_12,
            hint="size-* utilities; the file's own width and height are dropped",
        ),
        panel(
            "Colour",
            inherited,
            muted,
            accent,
            danger,
            hint="text-* colours an SVG that paints with currentColor",
        ),
        panel("Glyphs", check, plus, arrow_right, trash, star, calendar),
        panel(
            "Accessible name",
            decorative,
            labelled,
            in_an_icon_button,
            hint="Same pixels, different markup",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'An `Icon` is `aria-hidden="true"` unless it has an `aria-label`, a `role` '
            "or its own `aria-hidden`, so a decorative icon stays out of the "
            "accessibility tree.",
        ),
        Note(
            "a11y",
            'An icon that means something on its own needs `role("img")` and '
            "`aria_label()`. In an icon-only `Button`, name the button with "
            "`icon_only()` instead.",
        ),
        Note(
            "note",
            "`directory_resolver` raises a `ValueError` for a name that resolves "
            "outside its folder, such as `../secret`. The markup is inlined "
            "unescaped, so this keeps a name taken from a request from "
            "reaching another SVG on disk.",
        ),
        Note(
            "warn",
            "The SVG is inlined as it is, so a resolver that returns SVG from "
            "users puts their markup in your page. Resolve only markup you trust.",
        ),
        Note(
            "note",
            "An `Icon` adds the SVG namespace (`xmlns`) when the file leaves it "
            "out, so the markup stays valid outside an HTML page.",
        ),
    ],
    related=[Button, Avatar],
)
