from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Switch

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Keyboard shortcuts"),
        pr.lead(
            "A shortcut is declared once, on the thing it runs. Hue draws the "
            "keys next to it and binds the same keys for the whole page, so "
            "what a reader sees is always what works."
        ),
        pr.h2("Declaring one"),
        pr.p(
            "Three things take a shortcut: a CommandItem, a MenuItem, and the "
            "Command palette itself, whose hotkey opens and closes it."
        ),
        pr.code(
            'Command().hotkey("mod+k").content(\n'
            '    CommandItem().label("Go to Billing")\n'
            '    .shortcut("g", "b")\n'
            '    .href("/billing"),\n'
            '    CommandItem().label("Create invoice")\n'
            '    .shortcut("alt+n")\n'
            '    .action(call("createInvoice")),\n'
            ")\n\n"
            'MenuItem().content("Duplicate").shortcut("mod+d")'
        ),
        pr.p(
            "A shortcut works anywhere on the page, whether the palette or "
            "menu it belongs to is open or not. Pressing it does exactly "
            "what picking the item would: a link is followed, an action runs, "
            "and an open palette or menu closes. Linear and VS Code treat the "
            "shortcuts in their palettes the same way, as does a desktop menu "
            "bar: the list is where people learn a shortcut, and they use it "
            "without opening the list."
        ),
        pr.h2("Writing the keys"),
        pr.p(
            "Each argument is one key press. The keys of a chord, pressed "
            "together, are joined with a plus sign. Several arguments are a "
            "sequence, pressed one after another, each within a second of the "
            "last. This is the notation Mousetrap, tinykeys and GitHub's "
            "hotkey library use."
        ),
        pr.code(
            'shortcut("mod+k")        # Command-K on a Mac, Control-K elsewhere\n'
            'shortcut("alt+shift+n")  # three keys, together\n'
            'shortcut("g", "b")       # G, then B\n'
            'shortcut("?")            # a single key'
        ),
        pr.bullets(
            [
                pr.p(
                    "mod is the Command key on Apple platforms and Control "
                    "everywhere else. Use it rather than ctrl for a shortcut "
                    "that should feel native on both. ctrl is always Control, "
                    "which on a Mac is a different key from Command."
                ),
                pr.p(
                    "The modifiers are mod, ctrl, alt and shift. Alt is Option "
                    "on a Mac. Letters and digits are matched by the key that "
                    "was pressed rather than the character it typed, so "
                    "alt+n works even though Option-N types a tilde."
                ),
                pr.p(
                    "Named keys use the names Kbd draws: enter, esc, tab, "
                    "space, backspace, delete, up, down, left and right. "
                    "Letters can be written in either case."
                ),
                pr.p(
                    "A shortcut Hue could never match, such as a modifier on "
                    "its own or an unknown modifier like cmd, raises an error "
                    "when it is declared, so a typo cannot fail silently in "
                    "the browser."
                ),
            ]
        ),
        pr.h2("While someone is typing"),
        pr.p(
            "A shortcut made only of letters, digits or other plain keys is "
            "ignored while focus is in a text field, a select or anything "
            'editable. Otherwise typing the word "gb" into a comment box '
            "would leave the page. A shortcut with mod, ctrl or alt in it "
            "still works in a field, which is why a palette's hotkey "
            "normally has one."
        ),
        pr.h2("Letting people switch them off"),
        pr.p(
            "Single-key shortcuts are a problem for people who use speech "
            "input, where a spoken word arrives as a string of key presses, "
            "and for anyone who presses keys by accident. WCAG 2.1.4 "
            "(Character Key Shortcuts) requires that shortcuts like these "
            "can be turned off. Hue keeps that setting in an Alpine store, "
            "$store.shortcuts.letters, and remembers it in the browser. "
            "Shortcuts with a modifier are not affected."
        ),
        pr.p(
            "Put a switch for it in your app's settings. It needs nothing "
            "but the binding:"
        ),
        pr.code(
            'Switch().name("letter_shortcuts")\n'
            '.label("Single-key shortcuts")\n'
            '.description("Such as G then B to go to Billing.")\n'
            '.x_model("$store.shortcuts.letters")'
        ),
        Switch()
        .name("letter_shortcuts")
        .label("Single-key shortcuts")
        .description("Such as G then B to go to Billing. Try it on this page.")
        .x_model("$store.shortcuts.letters"),
        pr.h2("When two things claim the same keys"),
        pr.p(
            "The first one in the document wins, and the others never hear "
            "the keys. Shortcuts are registered for as long as their element "
            "is on the page, so a fragment that replaces a menu takes its "
            "old shortcuts with it and brings its own. An item that is "
            "disabled is skipped, and the keys go to the next one that "
            "claims them, if there is one."
        ),
        pr.p(
            "A sequence and a single key can collide in one direction: if g "
            "is a shortcut of its own, it runs on the first press and g then "
            "b never gets its second. Keep single keys out of the letters "
            "your sequences start with."
        ),
        Alert()
        .variant("warning")
        .title("Keys the browser keeps")
        .content(
            pr.p(
                "Some chords never reach the page, whatever it asks. In "
                "Chrome these include mod+n, mod+shift+n, mod+t, mod+shift+t "
                "and mod+w, which open and close windows and tabs, and on a "
                "Mac mod+q and mod+h belong to the system. A shortcut on one "
                "of them is drawn but does nothing. Prefer alt or a sequence "
                "for an app's own commands."
            )
        ),
        pr.h2("What a screen reader hears"),
        pr.p(
            "Each key is drawn with Kbd, which gives a modifier its spoken "
            "name, so the command key is read as Command rather than as the "
            "name of its glyph. Between the presses of a sequence a screen "
            'reader hears "then". A chord is also written into '
            "aria-keyshortcuts on the item, with the platform's own key for "
            "mod, which is how assistive technology learns about a shortcut "
            "without reading the row. A sequence has no way to be written "
            "there, so it is only drawn."
        ),
        pr.h2("Shortcuts that are only shown"),
        pr.p(
            "Tooltip has a shortcut() too, and it takes a Kbd rather than "
            "keys, because it describes the key of the control it sits on "
            "and binds nothing. Bind the key where the action is, on the "
            "palette or the item, and let the tooltip say what it is. "
            "Binding it twice would run it twice, and a hotkey that toggles "
            "a palette would open it and close it again."
        ),
    )


PAGE = ProsePage(
    slug="keyboard-shortcuts",
    title="Keyboard shortcuts",
    nav_label="Keyboard shortcuts",
    group="Guides",
    order=5,
    build=_build,
)
