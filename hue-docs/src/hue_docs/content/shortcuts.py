from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Kbd, Switch

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Keyboard shortcuts"),
        pr.lead(
            "An app declares its shortcuts once, in a registry. Every page binds "
            "them, so they work anywhere, and the command palette and menus "
            "that show one refer to it rather than repeating its keys. What a "
            "reader sees next to an item is always what works."
        ),
        pr.p(
            "This site has four. Press ",
            Kbd("G"),
            " then ",
            Kbd("K"),
            " on any page to come back here, ",
            Kbd("G"),
            " then ",
            Kbd("C"),
            " for the Command page, ",
            Kbd("G"),
            " then ",
            Kbd("H"),
            " for the introduction, and ",
            Kbd("alt", "C"),
            " to copy a link to the page you are on.",
        ),
        pr.h2("Declaring them"),
        pr.p(
            "A registry is a class whose attributes are Shortcut objects. It is "
            "a class rather than a list so that everything else refers to "
            "Shortcuts.create_invoice, which a type checker can follow and a "
            "rename updates. Hand it to create_page_base, and every page made "
            "from that base binds it."
        ),
        pr.code(
            "from hue.js import call\n"
            "from hue.pages import create_page_base\n"
            "from hue.shortcuts import Shortcut, ShortcutRegistry\n\n\n"
            "class Shortcuts(ShortcutRegistry):\n"
            "    billing = Shortcut(\n"
            '        "Go to Billing", "g", "b",\n'
            '        href="/billing/", group="Navigate",\n'
            "    )\n"
            "    create_invoice = Shortcut(\n"
            '        "Create invoice", "alt+n",\n'
            '        action=call("createInvoice"),\n'
            "    )\n\n\n"
            "Page = create_page_base(\n"
            '    css_url="/static/hue/styles.css",\n'
            '    js_url="/static/hue/js/alpine.js",\n'
            "    html_title_factory=str,\n"
            "    shortcuts=Shortcuts,\n"
            ")"
        ),
        pr.p(
            "A Shortcut takes its label, its keys, and either an href or an "
            "action. The href can be a function of the request, for a URL that "
            "has to be reversed per request. The action is an Alpine "
            "expression, built with call() or unsafe(). group, icon, "
            "description and keywords are for the palette that lists it."
        ),
        pr.p(
            "Pressing a shortcut does what clicking a link to the href, or a "
            "button running the action, would do. The page renders one of each, "
            "hidden, for every shortcut, and the keys click it."
        ),
        pr.h2("Checked when the app starts"),
        pr.p(
            "Defining the registry checks the whole set. Two shortcuts on the "
            "same keys raise an error that names both, and so do mod+k and "
            "ctrl+k, which are the same press away from Apple platforms. So "
            "does a shortcut whose keys start another's: if g runs on its own, "
            "g then b could never be finished. A Command's hotkey is checked "
            "against the page's registry when the palette renders."
        ),
        pr.h2("Writing the keys"),
        pr.p(
            "Each key argument is one key press. The keys of a chord, pressed "
            "together, are joined with a plus sign. Several arguments are a "
            "sequence, pressed one after another, each within a second of the "
            "last. This is the notation Mousetrap, tinykeys and GitHub's hotkey "
            "library use."
        ),
        pr.code(
            "# Command-K on a Mac, Control-K elsewhere\n"
            'Shortcut("Search", "mod+k", ...)\n\n'
            "# three keys, together\n"
            'Shortcut("Archive", "alt+shift+a", ...)\n\n'
            "# G, then B\n"
            'Shortcut("Billing", "g", "b", ...)\n\n'
            "# a single key\n"
            'Shortcut("Help", "?", ...)'
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
                    "was pressed rather than the character it typed, so alt+n "
                    "works even though Option-N types a tilde."
                ),
                pr.p(
                    "Named keys use the names Kbd draws: enter, esc, tab, "
                    "space, backspace, delete, up, down, left and right. "
                    "Letters can be written in either case."
                ),
                pr.p(
                    "Keys Hue could never match, such as a modifier on its own "
                    "or an unknown modifier like cmd, raise an error when the "
                    "Shortcut is made."
                ),
            ]
        ),
        pr.h2("Showing them"),
        pr.p(
            "CommandShortcuts, placed in a Command, lists every shortcut that is "
            "on for the page, in groups by their group, with the keys at the "
            "end of each row. A MenuItem given a shortcut shows its keys, does "
            "what it does, and takes its label when it has no content of its "
            "own."
        ),
        pr.code(
            'Command().hotkey("mod+k").content(CommandShortcuts())\n\n'
            "DropdownMenu().content(\n"
            "    MenuItem().shortcut(Shortcuts.create_invoice),\n"
            ")"
        ),
        pr.p(
            "Neither binds the keys again: the page has bound them already, so "
            "they work with the palette and the menu closed. A menu item that "
            "shows a shortcut the page does not bind raises an error, since it "
            "would show keys that do nothing."
        ),
        pr.h2("Shortcuts for one page"),
        pr.p(
            "Some shortcuts only make sense on some pages: archiving an invoice "
            "means something on an invoice and nothing on the dashboard. "
            "Declare these in the registry with scoped=True, so they are typed "
            "and checked against the rest like any other, and switch them on "
            "from the handler that builds the page with shortcuts.use(). It "
            "works the way toast.success() does. There is nothing to pass "
            "along, because the router opens and closes the request's list."
        ),
        pr.code(
            "class Shortcuts(ShortcutRegistry):\n"
            "    archive = Shortcut(\n"
            '        "Archive invoice", "e", scoped=True, group="This invoice",\n'
            "    )\n\n\n"
            "from hue import shortcuts\n\n"
            "def index(self, request, context, id: int):\n"
            "    shortcuts.use(\n"
            "        Shortcuts.archive,\n"
            '        action=call("archiveInvoice", id),\n'
            "    )\n"
            "    return Page(...)"
        ),
        pr.p(
            "use() can give the shortcut what it does on this page, as here, "
            "or leave it to the href or action the Shortcut was declared with. "
            "It takes effect on the page the handler returns. A fragment "
            "response cannot add a shortcut to a page that is already open, "
            "and calling use() outside a request raises an error."
        ),
        pr.h2("While someone is typing"),
        pr.p(
            "A shortcut made only of letters, digits or other plain keys is "
            "ignored while focus is in a text field, a select or anything "
            'editable. Otherwise typing the word "gb" into a comment box '
            "would leave the page. A shortcut with mod, ctrl or alt in it still "
            "works in a field, which is why a palette's hotkey normally has one."
        ),
        pr.h2("Letting people switch them off"),
        pr.p(
            "Single-key shortcuts are a problem for people who use speech "
            "input, where a spoken word arrives as a string of key presses, and "
            "for anyone who presses keys by accident. WCAG 2.1.4 (Character Key "
            "Shortcuts) requires that shortcuts like these can be turned off. "
            "Hue keeps that setting in an Alpine store, $store.shortcuts.letters, "
            "and remembers it in the browser. Shortcuts with a modifier are not "
            "affected."
        ),
        pr.p(
            "Put a switch for it in your app's settings. It needs nothing but "
            "the binding:"
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
        .description("Such as G then K to come back here. Try it on this page.")
        .x_model("$store.shortcuts.letters"),
        Alert()
        .variant("warning")
        .title("Keys the browser keeps")
        .content(
            pr.p(
                "Some chords never reach the page, whatever it asks. In Chrome "
                "these include mod+n, mod+shift+n, mod+t, mod+shift+t and "
                "mod+w, which open and close windows and tabs, and on a Mac "
                "mod+q and mod+h belong to the system. A shortcut on one of them "
                "is drawn but does nothing. Prefer alt or a sequence for an "
                "app's own commands."
            )
        ),
        pr.h2("What a screen reader hears"),
        pr.p(
            "Each key is drawn with Kbd, which gives a modifier its spoken "
            "name, so the command key is read as Command rather than as the "
            "name of its glyph. Between the presses of a sequence a screen "
            'reader hears "then". A chord is also written into '
            "aria-keyshortcuts on the row that shows it, with the platform's "
            "own key for mod, which is how assistive technology learns about a "
            "shortcut without reading the row. A sequence has no way to be "
            "written there, so it is only drawn."
        ),
        pr.h2("Shortcuts that are only shown"),
        pr.p(
            "Tooltip has a shortcut() too, and it takes a Kbd, because it "
            "describes the key of the control it sits on and binds nothing. "
            "Bind the key in the registry, or as a palette's hotkey, and let the "
            "tooltip say what it is. Binding it twice would run it twice, and a "
            "hotkey that toggles a palette would open it and close it again."
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
