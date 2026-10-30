from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Kbd, Text

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def in_a_sentence() -> Text:
    return Text("Press ").content(Kbd("mod", "K"), " to open the command menu.")


# Anatomy


def chord() -> Kbd:
    return Kbd("mod", "K")


def three_keys() -> Kbd:
    return Kbd("shift", "mod", "P")


def named_key() -> Kbd:
    return Kbd("esc")


def arrows() -> ComponentType:
    return html.span(Kbd("up"), " or ", Kbd("down"))


def enter() -> Kbd:
    return Kbd("enter")


def function_key() -> Kbd:
    return Kbd("f5")


def single_letter() -> Kbd:
    return Kbd("g")


def letter_in_a_chord() -> Kbd:
    return Kbd("ctrl", "g")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "`Kbd` takes the keys of one chord as arguments and draws each as its "
            "own `kbd` element, side by side inside a `span`. `keys()` replaces them "
            "later in a chain."
        ),
        pr.code('Kbd("mod", "K")\nKbd("shift", "mod", "P")\nKbd("esc")'),
        pr.h3("Key names Kbd understands"),
        pr.p(
            "`mod`, `shift`, `alt` and `ctrl` are the modifiers, described in the "
            "next section. `esc`, `enter`, `tab`, `space`, `backspace`, "
            "`delete`, `up`, `down`, `left`, `right`, `home`, `end`, `pageup` and "
            "`pagedown` are drawn as "
            "their glyph or short name. Every name is matched in any case. "
            "Anything else is printed as given, with two rules for letters: a "
            'letter on its own is drawn as written, so `Kbd("g")` shows `g`, and '
            'a letter in a chord is drawn as a capital, so `Kbd("ctrl", "g")` '
            "shows `G`. A function key, `f1` to `f12`, is always a capital."
        ),
        pr.h3("Modifier keys in Kbd"),
        pr.p(
            "`mod` is Command on Apple platforms and Control everywhere else. On "
            "Apple platforms the modifiers are drawn as glyphs: ⌘ for `mod`, ⇧ "
            "for `shift`, ⌥ for `alt` and ⌃ for `ctrl`. Elsewhere they are words: "
            "`mod` and `ctrl` are both drawn as Ctrl, `alt` as Alt and `shift` as "
            "Shift."
        ),
        pr.p(
            "The server cannot tell the platform, so `Kbd` renders the glyphs and "
            "Alpine swaps in the words in the browser, reading the platform from "
            "the shortcuts store in hue's bundle. Without hue's bundle the glyphs "
            "stay."
        ),
        pr.h3("A sequence of key presses"),
        pr.p(
            "One `Kbd` is one chord. For a shortcut pressed as a sequence, such "
            "as G then B, put one `Kbd` per press side by side."
        ),
        pr.code('html.span(Kbd("g"), " then ", Kbd("b"))'),
    )


PAGE = ComponentPage(
    Kbd,
    lede=(
        "`Kbd` draws keyboard keys as real `kbd` elements, for a shortcut written "
        "into a sentence, a menu or a hint. Modifiers are drawn as glyphs on Apple "
        "platforms and as words elsewhere, and `mod` becomes Command or Control "
        "to match the reader's platform."
    ),
    usage=_usage,
    panels=[
        panel("Live", in_a_sentence, layout="center"),
        panel(
            "Anatomy",
            chord,
            three_keys,
            named_key,
            arrows,
            enter,
            function_key,
            single_letter,
            letter_in_a_chord,
        ),
    ],
    notes=[
        Note(
            "a11y",
            "A key drawn as a glyph, such as ⇧ or ↵, hides the glyph from "
            "screen readers and carries its spoken name (Shift, Enter) in "
            "visually hidden text, so the glyph's Unicode name is never read.",
        ),
        Note(
            "a11y",
            "Each modifier is announced by its name, matching the key drawn: "
            "`mod` as Command or Control, `ctrl` as Control, `alt` as Alt and "
            "`shift` as Shift.",
        ),
        Note(
            "note",
            "Each key is its own `kbd` element, wrapped in one `span` that takes "
            "`class_()` and the other attributes.",
        ),
    ],
    related=[Text],
)
