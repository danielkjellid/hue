from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.layout import prose as pr
from hue_docs.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Theming"),
        pr.lead(
            "A `Theme` restyles Hue from Python. It is made of groups, one per "
            "part of the design, and every field in a group is optional: what "
            "a `Theme` leaves out keeps Hue's value."
        ),
        pr.h2("Giving an app a Theme"),
        pr.p(
            "Build a `Theme` once and hand it to the page. Each integration "
            "takes it in the place it takes the rest of its page settings."
        ),
        pr.bullets(
            [
                "`hue-django` reads the `HUE_THEME` setting.",
                "`hue-fastapi` takes `configure_hue(app, theme=...)`.",
                "Without either, `create_page_base(theme=...)` binds it to the "
                "`Page` class it returns.",
            ]
        ),
        pr.code(
            "from hue.palette import Color\n"
            "from hue.theme import Accent, Corners, Fonts, Surfaces, Theme\n\n"
            "THEME = Theme(\n"
            "    accent=Accent(\n"
            '        fill=Color("#6D28D9", dark="#8B5CF6"),\n'
            '        fg=Color("#FFFFFF", dark="#0B0614"),\n'
            "    ),\n"
            '    surfaces=Surfaces(base=Color("#FFFFFF", dark="#18181B")),\n'
            "    fonts=Fonts(ui='\"Geist\", sans-serif'),\n"
            '    corners=Corners(control="6px", container="10px"),\n'
            ")"
        ),
        pr.p(
            "A colour is a `hue.palette` `Color`. One with a `dark` value "
            "changes between the modes, and one without holds in both. The page "
            "writes the `Theme` as a `<style>` element after Hue's stylesheet "
            "and before any stylesheet the app adds, so the app's own CSS still "
            "has the last word."
        ),
        pr.h2("The groups of a Theme"),
        pr.bullets(
            [
                "`accent` is an `Accent`: `fill` for a primary button and "
                "anything selected, `fg` for the text on it, `hover` and "
                "`active`, `subtle` and `subtle_hover` for tinted backgrounds, "
                "`border`, `text` for links, and `vivid` for decoration.",
                "`success`, `warning` and `info` are each a `Status`: `fill`, "
                "`text`, `subtle`, `border` and `vivid`. `danger` is a "
                "`Danger`, which adds `hover` and `fg`, because a danger button "
                "uses them.",
                "`surfaces` is a `Surfaces`: `canvas` and `canvas_subtle` for "
                "the page, `base` for cards and panels, `raised` for popovers "
                "and menus, `sunken` for wells, `hover` and `active` for rows, "
                "`inverse` and `inverse_fg` for a tooltip, and `scrim` behind a "
                "dialog.",
                "`text` is a `Text`: `default`, `strong`, `muted`, `subtle` and "
                "`disabled`.",
                "`borders` is a `Borders`: `default`, `strong`, `input` and `hover`.",
                "`categories` is a `Categories`, the six colours charts and "
                "calendars draw with: `accent`, `teal`, `orange`, `purple`, "
                "`yellow` and `gray`.",
                "`fonts` is a `Fonts`: `ui` for controls and headings, `body` "
                "for running text, `mono` for code. Hue loads no webfonts, so "
                "load the faces you name.",
                "`corners` is a `Corners`, a radius by what it rounds: `small` "
                "for a checkbox or a swatch, `item` for a row in a menu or a "
                "badge, `control` for a button or a field, `container` for a "
                "card or a popover, and `overlay` for a dialog or a drawer.",
            ]
        ),
        pr.h2("Building a tone from a scale"),
        pr.p(
            "`Accent.from_scale()`, `Status.from_scale()` and "
            "`Danger.from_scale()` fill a whole tone from ten colours, the "
            "steps 50 to 900 from lightest to darkest. Each method's docstring "
            "lists the step every field reads. For the accent, `fill` is 700 "
            "in light mode and 500 in dark, and `subtle` is 50 in light mode "
            "and the 500 step at 14% in dark. `fg` is left at Hue's value, so "
            "set it to a colour that reads on your fill. Change any other "
            "field afterwards with `dataclasses.replace`."
        ),
        pr.code(
            "from dataclasses import replace\n\n"
            "from hue.palette import Color\n"
            "from hue.theme import Accent\n\n"
            "accent = Accent.from_scale(\n"
            "    [\n"
            '        "#F5F3FF", "#EDE9FE", "#DDD6FE", "#C4B5FD", "#A78BFA",\n'
            '        "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95",\n'
            "    ]\n"
            ")\n"
            'accent = replace(accent, fg=Color("#FFFFFF", dark="#0B0614"))'
        ),
        pr.h2("What a Theme refuses"),
        pr.p(
            "A scale with other than ten steps raises a `ValueError`, and so "
            "does a value that is not spelled like a colour, a font stack or a "
            "length. The values are written into the page as CSS, so a "
            "semicolon, a brace or an angle bracket is refused rather than "
            "allowed to end the rule."
        ),
    )


PAGE = GuidePage(
    slug="theming",
    title="Theming",
    nav_label="Theming",
    group="Guides",
    order=5,
    build=_build,
)
