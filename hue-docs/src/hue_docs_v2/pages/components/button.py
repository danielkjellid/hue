from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Button, ButtonGroup, SegmentedControl, Stack

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def new_project() -> Button:
    return Button().content(Icon("plus"), "New project")


# Variants


def primary() -> Button:
    return Button().variant("primary").content("Publish")


def secondary() -> Button:
    return Button().variant("secondary").content("Publish")


def outline() -> Button:
    return Button().variant("outline").content("Preview")


def ghost() -> Button:
    return Button().variant("ghost").content("Cancel")


def link() -> Button:
    return Button().variant("link").content("View changes")


def danger() -> Button:
    return Button().variant("danger").content("Delete")


def danger_outline() -> Button:
    return Button().variant("danger-outline").content("Delete")


# Sizes


def xs() -> Button:
    return Button().size("xs").content("Save")


def sm() -> Button:
    return Button().size("sm").content("Save")


def md() -> Button:
    return Button().size("md").content("Save")


def lg() -> Button:
    return Button().size("lg").content("Save")


# Anatomy


def label_only() -> Button:
    return Button().variant("outline").content("Export")


def icon_and_label() -> Button:
    return Button().variant("outline").content(Icon("arrow-right"), "Continue")


def icon_only() -> Button:
    return Button().variant("outline").icon_only("Delete").content(Icon("trash"))


def pill() -> Button:
    return Button().pill().content(Icon("plus"), "Add")


# States


def enabled() -> Button:
    return Button().content("Save")


def disabled() -> Button:
    return Button().disabled().content("Save")


def loading() -> Button:
    return Button().loading().content("Save")


def loading_outline() -> Button:
    return Button().variant("outline").loading().content("Export")


# Width


def fluid() -> ComponentType:
    return Stack().content(
        Button().fluid().content("Sign in"),
        Button().variant("ghost").fluid().content("Create an account"),
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Button is a native button element. Its children are its "
            "content, so text and icons go in content(), and the modifiers set "
            "how it looks. variant() defaults to primary and size() to md."
        ),
        pr.code(
            'Button().variant("outline").size("sm").content(Icon("plus"), "Add row")'
        ),
        pr.h3("Submitting a form"),
        pr.p(
            'A Button renders type="button" unless you set another type, so a '
            "Button inside a form does not submit it by accident. Set "
            'type("submit") on the one that should. formaction() sends a '
            "submit button's form somewhere other than the form's own action, "
            "which lets one form post to more than one place."
        ),
        pr.code(
            'html.form().method("POST").action("/invoices/").content(\n'
            "    ...,\n"
            '    Button().type("submit").content("Save"),\n'
            '    Button().variant("ghost").type("submit")'
            '.formaction("/invoices/draft/").content("Save as draft"),\n'
            ")"
        ),
        pr.h3("Buttons that hold only an icon"),
        pr.p(
            "icon_only() makes the button square and takes the accessible name "
            "as its argument. An icon has no text for a screen reader to read, "
            "so the signature requires the name."
        ),
        pr.h3("Work in flight"),
        pr.p(
            "loading() shows a spinner over the label and disables the button, "
            "so a second click cannot submit twice. The label stays in place "
            "with zero opacity, which keeps both the button's width and its "
            "accessible name from changing, and aria-busy announces the state."
        ),
    )


PAGE = ComponentPage(
    Button,
    lede=(
        "A button runs an action or submits a form. Seven variants cover the "
        "roles from the main action on a page to a link in a sentence, in four "
        "sizes that match the height of the form controls beside them."
    ),
    usage=_usage,
    panels=[
        panel("Live", new_project, layout="center", hint="Hover, focus and press it"),
        panel(
            "Variants",
            primary,
            secondary,
            outline,
            ghost,
            link,
            danger,
            danger_outline,
        ),
        panel("Sizes", xs, sm, md, lg, hint="The same heights as the form controls"),
        panel("Anatomy", label_only, icon_and_label, icon_only, pill),
        panel("States", enabled, disabled, loading, loading_outline),
        panel("Width", fluid, layout="stack", hint="fluid() fills its container"),
    ],
    notes=[
        Note(
            "a11y",
            "icon_only() takes the accessible name as its argument and sets "
            "aria-label from it, so an unnamed icon button cannot be written.",
        ),
        Note(
            "a11y",
            "loading() sets aria-busy and keeps the label in the accessibility "
            "tree, so a screen reader still hears what the button is.",
        ),
        Note(
            "a11y",
            "The focus ring shows on keyboard focus only (focus-visible), never "
            "on a mouse click.",
        ),
        Note(
            "note",
            "disabled() renders the native disabled attribute, which also takes "
            "the button out of the tab order.",
        ),
        Note(
            "warn",
            'A Button is type="button" by default. A form needs one with '
            'type("submit") to submit on click or on Enter.',
        ),
    ],
    related=[ButtonGroup, SegmentedControl],
)
