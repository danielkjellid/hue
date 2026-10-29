from __future__ import annotations

from hue.js import close
from hue.types.core import ComponentType
from hue.ui import Button, Checkbox, Dialog, DropdownMenu, Popover, TextInput, Tooltip

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def share() -> Popover:
    return (
        Popover()
        .title("Share Route planner")
        .description("Anyone with the link can view. Members can edit.")
        .trigger(Button().variant("outline").content("Share project"))
        .content(
            TextInput()
            .name("share_link")
            .label("Share link")
            .hidden_label()
            .value("hue.app/p/9f2Kd8")
            .readonly()
            .action(Button().variant("outline").content("Copy")),
            Checkbox().name("allow_comments").label("Allow comments"),
        )
    )


# Placements


def bottom_start() -> Popover:
    return (
        Popover()
        .fit()
        .placement("bottom-start")
        .title("Bottom start")
        .trigger(Button().variant("outline").size("sm").content("bottom-start"))
    )


def bottom_end() -> Popover:
    return (
        Popover()
        .fit()
        .placement("bottom-end")
        .title("Bottom end")
        .trigger(Button().variant("outline").size("sm").content("bottom-end"))
    )


def top_start() -> Popover:
    return (
        Popover()
        .fit()
        .placement("top-start")
        .title("Top start")
        .trigger(Button().variant("outline").size("sm").content("top-start"))
    )


def top_end() -> Popover:
    return (
        Popover()
        .fit()
        .placement("top-end")
        .title("Top end")
        .trigger(Button().variant("outline").size("sm").content("top-end"))
    )


# Anatomy


def title_and_description() -> Popover:
    return (
        Popover()
        .title("Monthly recurring revenue")
        .description("Annual plans are divided by 12.")
        .trigger(
            Button()
            .variant("ghost")
            .icon_only("What is MRR?")
            .content(Icon("circle-info"))
        )
    )


def with_content() -> Popover:
    return (
        Popover()
        .title("Rename")
        .trigger(Button().variant("outline").content("Rename"))
        .content(
            TextInput().name("project_name").label("Name").value("Atlas"),
            Button().size("sm").content("Save").on_click(close()),
        )
    )


def fit_to_content() -> Popover:
    return (
        Popover()
        .fit()
        .label("Help")
        .trigger(Button().variant("outline").content("Help"))
        .content(
            Button().variant("link").content("Read the guide").on_click(close()),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Popover` renders its trigger and a panel anchored to it. A "
            "click on the trigger opens and closes the panel. `title()` and "
            "`description()` head the panel, and anything passed to `content()` "
            "follows underneath."
        ),
        pr.code(
            "(\n"
            "    Popover()\n"
            '    .title("Share Route planner")\n'
            '    .trigger(Button().variant("outline").content("Share project"))\n'
            '    .content(Checkbox().name("allow_comments").label("Allow comments"))\n'
            ")"
        ),
        pr.p(
            "`trigger()` takes a hue component rather than plain markup, because "
            "the `Popover` writes the click handler, `aria-expanded`, "
            "`aria-controls` and the anchor onto that control."
        ),
        pr.h2("Popover is not modal"),
        pr.p(
            "Nothing is trapped and the page behind stays live, so a form "
            "inside a `Popover` is part of the page and Tab moves on past the "
            "panel. Escape closes the `Popover` and puts focus back on the "
            "trigger. A click outside closes it and leaves focus where the "
            "click landed."
        ),
        pr.h3("Closing from inside"),
        pr.p(
            "The `Popover` puts `close()` in scope for everything inside it. Pass "
            "`close()` from `hue.js` to `on_click()` on a control in the panel. "
            "Inside a `Popover` that sits in a `Dialog`, `close()` closes the "
            "`Popover` and leaves the `Dialog` open."
        ),
        pr.h2("Popover placement and width"),
        pr.p(
            "`placement()` names the corner of the trigger the panel hangs "
            'from: `"bottom-start"` (the default), `"bottom-end"`, `"top-start"` or '
            '`"top-end"`. The panel flips and shifts to stay inside the viewport, '
            "so the placement is a preference. The panel is 280px wide; `fit()` "
            "sizes it to its content instead, for a short line or a few links."
        ),
    )


PAGE = ComponentPage(
    Popover,
    lede=(
        "A `Popover` is a panel anchored to a control, for content a reader "
        "can interact with, such as a short form or a few links. It is not "
        "modal, so the page behind stays live."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            share,
            layout="center",
            min_height=320,
            hint="Open it, tab into it, press Escape",
        ),
        panel(
            "Placements",
            bottom_start,
            bottom_end,
            top_start,
            top_end,
            layout="center",
            min_height=240,
            captions=False,
            hint="Flips when there is no room",
        ),
        panel(
            "Anatomy",
            title_and_description,
            with_content,
            fit_to_content,
            min_height=360,
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The panel has `role="dialog"` and is named by its title through '
            "`aria-labelledby`, or by `label()` when it has no title. The trigger "
            "gets `aria-haspopup`, `aria-expanded` and `aria-controls`.",
        ),
        Note(
            "a11y",
            "Escape closes the `Popover` and returns focus to the trigger. The "
            "listener sits on the `Popover` and stops the key, so inside a "
            "`Dialog` only the `Popover` closes.",
        ),
        Note(
            "note",
            "A `Popover` with neither `title()` nor `label()` raises an error when "
            "it renders.",
        ),
        Note(
            "warn",
            "Focus is not trapped. A keyboard user tabs into the panel from "
            "the trigger and out of it onto the rest of the page.",
        ),
    ],
    related=[Tooltip, DropdownMenu, Dialog],
)
