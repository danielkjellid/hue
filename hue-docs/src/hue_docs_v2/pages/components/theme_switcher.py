from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import SegmentedControl, ThemeSwitcher

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def switch_this_frame() -> ThemeSwitcher:
    return ThemeSwitcher()


# Anatomy


def icons() -> ThemeSwitcher:
    return ThemeSwitcher()


def labelled() -> ThemeSwitcher:
    return ThemeSwitcher().labelled()


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "`ThemeSwitcher` takes no content. It renders a small "
            "`SegmentedControl` with three options: light, dark and system. By "
            "default each option is an icon; `labelled()` writes the theme's name "
            "beside it."
        ),
        pr.code("ThemeSwitcher()\nThemeSwitcher().labelled()"),
        pr.h3("How ThemeSwitcher applies a theme"),
        pr.p(
            "A click calls the theme store in hue's Alpine bundle, which every "
            "hue `Page` loads. The store remembers the choice in `localStorage` "
            "and writes the resolved `light` or `dark` to `data-theme` on the "
            "`html` element, which is what hue's colour tokens switch on. The "
            "system option resolves against the operating system's colour "
            "scheme and keeps following it for as long as it stays selected."
        ),
        pr.p(
            "Each `Page` applies the remembered choice in a blocking script in "
            "its head, before the first paint, so a page in the dark theme "
            "never flashes light on load."
        ),
        pr.h3("Where ThemeSwitcher stores the choice"),
        pr.p(
            'The `localStorage` key is `"hue-theme"`. When one origin serves '
            "several hue apps that should each keep their own theme, give each "
            "app its own key with `create_page_base(theme_storage_key=...)`."
        ),
        pr.h3("ThemeSwitcher inside an iframe"),
        pr.p(
            "The store sets `data-theme` on the document it runs in, so a "
            "`ThemeSwitcher` in an iframe changes the theme of that frame only. "
            "The panels on this page are iframes: pressing dark in one turns "
            "that frame dark and leaves the rest of the page as it was. The "
            "frames share an origin and a storage key with this site, so the "
            "choice is also remembered for the site's next page load."
        ),
    )


PAGE = ComponentPage(
    ThemeSwitcher,
    lede=(
        "A theme switcher lets the reader pick light, dark or the system "
        "theme. The choice is remembered in the browser and applied before "
        "the first paint of every page that follows."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            switch_this_frame,
            layout="center",
            hint="Switches this frame's own theme",
        ),
        panel("Anatomy", icons, labelled),
    ],
    notes=[
        Note(
            "a11y",
            'The switcher is a group named `"Color theme"`. `aria_label()` on the '
            "`ThemeSwitcher` replaces that name.",
        ),
        Note(
            "a11y",
            "In the icon form each option is named after the theme it selects "
            '(`"Light theme"`, `"Dark theme"`, `"Match system"`), not after the icon '
            "it shows.",
        ),
        Note(
            "a11y",
            "The options are native buttons with `aria-pressed`, each its own "
            "Tab stop, pressed with Enter or Space.",
        ),
        Note(
            "note",
            "Which theme is selected is only known in the browser, so the "
            "server renders no option as pressed. Alpine marks the selected one "
            "when it starts.",
        ),
    ],
    related=[SegmentedControl],
)
