from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Button, Progress, Skeleton, Spinner

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Sizes


def xs() -> Spinner:
    return Spinner().size("xs")


def sm() -> Spinner:
    return Spinner().size("sm")


def md() -> Spinner:
    return Spinner().size("md")


def lg() -> Spinner:
    return Spinner().size("lg")


# Anatomy


def bare() -> Spinner:
    return Spinner()


def labelled() -> Spinner:
    return Spinner().label("Loading payments")


def muted() -> Spinner:
    return Spinner().muted()


def muted_and_labelled() -> Spinner:
    return Spinner().size("sm").muted().label("Searching")


def large_labelled() -> Spinner:
    return Spinner().size("lg").label("Preparing your report")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Spinner` is a spinning ring for work of unknown length. `size()` "
            "is `xs`, `sm`, `md` (the default) or `lg`, from 12px to 32px. `muted()` "
            "draws it grey instead of in the accent colour."
        ),
        pr.code('Spinner().label("Loading payments")'),
        pr.h3("Labels"),
        pr.p(
            "`label()` shows text beside the ring, sized to match the ring. "
            'Every `Spinner` is a `span` with `role="status"` holding an '
            "`aria-hidden` ring and a line of text, and that text is what a screen "
            "reader reads. Without a label the text is Loading, visually hidden."
        ),
        pr.p(
            "`label(..., visible=False)` keeps the label for screen readers only, "
            "for a spinner with no room for words beside it."
        ),
        pr.code('Spinner().label("Loading payments", visible=False)'),
        pr.h3("When it is announced"),
        pr.p(
            '`role="status"` is a polite live region. A `Spinner` that is on the '
            "page when the page loads is read in order, not announced. Screen "
            "readers announce a change to a live region that is already on the "
            "page, and they do not reliably announce one that arrives with its "
            "text, so a `Spinner` swapped in by Alpine AJAX may go unannounced."
        ),
        pr.h3("Inside a Button"),
        pr.p(
            "`Button` has its own `loading()` modifier, which draws a spinner over "
            "the label and disables the button. Use that instead of putting a "
            "`Spinner` in a `Button`'s content."
        ),
        pr.h3("Reduced motion"),
        pr.p(
            "The spin is a CSS animation. With reduced motion turned on, hue's "
            "stylesheet stops it, and the `Spinner` is a still ring with one "
            "darker arc."
        ),
    )


PAGE = ComponentPage(
    Spinner,
    lede=(
        "A `Spinner` shows that something is loading when there is no telling "
        "how long it will take. Give it a label, and it says what is loading "
        "both on screen and to a screen reader."
    ),
    usage=_usage,
    panels=[
        panel("Sizes", xs, sm, md, lg),
        panel(
            "Anatomy",
            bare,
            labelled,
            muted,
            muted_and_labelled,
            large_labelled,
        ),
    ],
    notes=[
        Note(
            "a11y",
            'Every `Spinner` renders `role="status"`, a polite live region that '
            "does not move focus.",
        ),
        Note(
            "a11y",
            "The ring is `aria-hidden`. A screen reader announces the text inside "
            "the region, which is the label, or a visually hidden Loading when "
            "there is none.",
        ),
        Note(
            "note",
            "The default text Loading is fixed English. Set `label()`, with "
            "`visible=False` if it should not show, to change it.",
        ),
    ],
    related=[Skeleton, Progress, Button],
)
