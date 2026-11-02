from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.layout import prose as pr
from hue_docs.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Theming"),
        pr.lead(
            "A `Theme` restyles Hue from Python. It names the tokens you want to "
            "change, and every token it leaves out keeps Hue's value."
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
            "from hue.theme import Ramp, Theme\n\n"
            "THEME = Theme(\n"
            "    accent=Ramp(\n"
            "        [\n"
            '            "#F5F3FF", "#EDE9FE", "#DDD6FE", "#C4B5FD", "#A78BFA",\n'
            '            "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95",\n'
            "        ]\n"
            "    ),\n"
            '    colors={"surface": Color("#FFFFFF", dark="#18181B")},\n'
            '    fonts={"ui": \'"Geist", sans-serif\'},\n'
            '    radii={"md": "6px"},\n'
            ")"
        ),
        pr.p(
            "The page writes the `Theme` as a `<style>` element after Hue's "
            "stylesheet and before any stylesheet the app adds, so the app's own "
            "CSS still has the last word."
        ),
        pr.h2("Replacing a tone's Ramp"),
        pr.p(
            "The accent and the four status tones (`success`, `warning`, "
            "`danger` and `info`) are each built on a `Ramp` of ten colours, "
            "the steps 50 to 900 from lightest to darkest. Passing a `Ramp` as "
            "`accent=` or a tone's name recolours every token of that tone in "
            "both modes, and leaves the other tones alone. The accent and info "
            "share Hue's blue by default, and replacing one does not move the "
            "other."
        ),
        pr.p(
            "Each token reads a fixed step. In light mode the accent is 700 and "
            "its subtle background is 50. In dark mode the accent is 500, and "
            "the subtle background and the border are the 500 step mixed with "
            "transparency. A ramp whose steps get darker in the same way as "
            "Hue's keeps the contrast Hue's own colours were chosen for."
        ),
        pr.h2("Setting a single token"),
        pr.p(
            "`colors` sets any of Hue's colour tokens by name: the surfaces "
            "(`canvas`, `surface`, `surface-raised`), the text colours (`fg`, "
            "`fg-muted`), the borders, each tone's tokens such as `accent-fg` or "
            "`danger-subtle`, and the category colours (`category-teal` and the "
            "rest) that charts and calendars draw with. The value is a "
            "`hue.palette` `Color`. A `Color` with a `dark` value changes "
            "between the modes, and one without holds in both."
        ),
        pr.p(
            "`fonts` sets `ui`, `body` and `mono` to a font stack, and `radii` "
            "sets `xs` to `xl` to a length. Hue loads no webfonts, so load the "
            "faces you name however your app loads its other assets."
        ),
        pr.p(
            "The grey surfaces, text and borders have no `Ramp` of their own. "
            "Several of their dark-mode values are not steps of Hue's grey, so "
            "set them as single tokens."
        ),
        pr.h2("What a Theme refuses"),
        pr.p(
            "A `Theme` raises a `ValueError` for a token name Hue does not have, "
            "a `Ramp` with other than ten steps, and a value that is not spelled "
            "like a colour, a font stack or a length. Its values are written "
            "into the page as CSS, so a semicolon, a brace or an angle bracket "
            "is refused rather than allowed to end the rule."
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
