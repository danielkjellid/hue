from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Kbd, Switch

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage
from hue_docs.shortcuts import Shortcuts


def _this_site() -> ComponentType:
    """
    The site's own shortcuts, read from its registry so the list cannot drift
    from the keys that work.
    """
    rows = []
    for shortcut in Shortcuts.shortcuts:
        presses: list[ComponentType] = []
        for index, step in enumerate(shortcut.steps):
            if index:
                presses.append(" then ")
            presses.append(Kbd(*step))
        rows.append(pr.p(*presses, f": {shortcut.label}"))
    return pr.bullets(rows)


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Keyboard shortcuts"),
        pr.lead(
            "An app declares its shortcuts once, in a registry. Every page binds "
            "them, so they work anywhere, and the command palette and menus "
            "that show one refer to it rather than repeating its keys. What a "
            "reader sees next to an item is always what works."
        ),
        pr.p("This site has its own, which work on every page:"),
        _this_site(),
        pr.h2("Declaring them"),
        pr.p(
            "A registry is a class whose attributes are Shortcut objects. It is "
            "a class rather than a list so that everything else refers to "
            "Shortcuts.create_invoice, which a type checker can follow and a "
            "rename updates."
        ),
        pr.code(
            "from hue.js import call\n"
            "from hue.shortcuts import Shortcut, ShortcutRegistry\n\n\n"
            "class Shortcuts(ShortcutRegistry):\n"
            "    billing = Shortcut(\n"
            '        "Go to Billing", "g", "b",\n'
            '        href="/billing/", group="Navigate",\n'
            "    )\n"
            "    create_invoice = Shortcut(\n"
            '        "Create invoice", "alt+n",\n'
            '        action=call("createInvoice"),\n'
            "    )"
        ),
        pr.p(
            "The registry goes in the render context, next to the date formats, "
            "so every render has it: a page binds it, and a palette or a menu "
            "returned in a fragment can still show its shortcuts. With "
            "hue-django it is a setting, a dotted path or the class itself:"
        ),
        pr.code('HUE_SHORTCUTS = "billing.shortcuts.Shortcuts"'),
        pr.p(
            "Anywhere else, put it in the HueContextArgs your router's "
            "_get_context_args returns, as shortcuts=Shortcuts."
        ),
        pr.p(
            "A Shortcut takes its label, its keys, and either an href or an "
            "action. The href can be a function of the request, for a URL that "
            "has to be reversed per request. The action is an Alpine "
            "expression, built with call() or unsafe(). group, icon, "
            "description and keywords are for the palette that lists it, and "
            "the icon is drawn by any row that shows the shortcut."
        ),
        pr.p(
            "Pressing a shortcut does what clicking a link to the href, or a "
            "button running the action, would do. Each page renders a hidden "
            "link or button for every shortcut, and the keys click it. Write an "
            "action for the page's Alpine scope, since that is where the keys "
            "run it: one that reaches a value only the palette or the menu "
            "holds would work when its row is clicked and not when its keys "
            "are pressed."
        ),
        pr.h2("Checked when the app starts"),
        pr.p(
            "Defining the registry checks the whole set. Two shortcuts on the "
            "same keys raise an error that names both, and so do mod+k and "
            "ctrl+k, which are the same press away from Apple platforms, and "
            "esc and escape, which are two names for one key. So does a "
            "shortcut found partway through another's sequence: if b runs on "
            "its own, g then b then c could never be finished. A Command's "
            "hotkey is checked against the registry when the palette renders. "
            "The registry refuses a shortcut named after one of its own "
            "methods, such as active or check."
        ),
        pr.p(
            "A key that ends another shortcut's sequence is fine. When both "
            "match what was just pressed, the longer one runs, so with b and g "
            "then b both declared, G then B runs the sequence and B on its own "
            "runs the key."
        ),
        pr.h2("Writing the keys"),
        pr.p(
            "Each key argument is one key press. The keys of a chord, pressed "
            "together, are joined with a plus sign. Several arguments are a "
            "sequence, pressed one after another, each within a second of the "
            "last. The chord notation is the one Mousetrap, tinykeys and "
            "GitHub's hotkey library use."
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
                    "on a Mac."
                ),
                pr.p(
                    "A key is a single ASCII character, a function key from f1 to "
                    "f12, or one of the names Kbd draws: esc, enter, tab, "
                    "space, backspace, delete, up, down, left, right, home, "
                    "end, pageup and pagedown. escape, return, del and the "
                    "arrowup family are read as the same keys. Letters can be "
                    "written in either case."
                ),
                pr.p(
                    "Shift changes which character a digit or a symbol types, "
                    "so write the character rather than the keys: ? rather "
                    "than shift+/. shift is only taken with a letter from a "
                    "to z, a function key or a named key."
                ),
                pr.p(
                    "tab, enter, space, esc, the arrows, home, end and the page "
                    "keys need mod, ctrl or alt. On their own they move focus, "
                    "press the focused control, scroll or close an overlay, "
                    "and a shortcut would take that away on every page."
                ),
                pr.p(
                    "alt goes with a letter, a digit or a named key, since "
                    "Option on a Mac turns a symbol into another character and "
                    "the key it was typed on cannot be told from the result."
                ),
                pr.p(
                    "A letter is matched by the character it types, so on an "
                    "AZERTY or Dvorak keyboard a shortcut follows the letters "
                    "printed on the keys. Two cases are matched by the key "
                    "pressed instead: Option on a Mac, since Option-N types a "
                    "tilde, and a layout without Latin letters, where Control-K "
                    "on a Russian keyboard types a Cyrillic letter."
                ),
                pr.p(
                    "Anything Hue could never match, such as a modifier on its "
                    "own, an unknown modifier like cmd, a misspelt key name or "
                    "the plus key, which is what joins the keys of a chord, "
                    "raises an error when the Shortcut is made."
                ),
            ]
        ),
        pr.h2("Showing them"),
        pr.p(
            "CommandShortcuts, placed in a Command, lists every shortcut that is "
            "on for the request, in groups by their group, with the keys at the "
            "end of each row. CommandItem and MenuItem take a shortcut() of "
            "their own: the row shows its keys, does what it does, and takes "
            "its label when it has none."
        ),
        pr.code(
            'Command().hotkey("mod+k").content(CommandShortcuts())\n\n'
            "DropdownMenu().content(\n"
            "    MenuItem().shortcut(Shortcuts.create_invoice),\n"
            ")"
        ),
        pr.p(
            "A row never binds the keys again, because the page has already "
            "bound them, so they work with the palette and the menu closed. It "
            "announces them instead, through aria-keyshortcuts."
        ),
        pr.p(
            "A row that runs a shortcut does nothing else. The keys only ever "
            "run the shortcut, so a row with an href or a click handler of its "
            "own would do one thing when clicked and another when its keys were "
            "pressed, and a disabled row would still run from the keyboard. "
            "Either raises an error, as does a checkable menu item. A shortcut "
            "that should not run on a page is scoped and left unused there. A "
            "row that shows a shortcut the request does not have on raises an "
            "error too, since it would show keys that do nothing."
        ),
        pr.h2("Shortcuts for one page"),
        pr.p(
            "Some shortcuts only make sense on some pages: archiving an invoice "
            "means something on an invoice and nothing on the dashboard. "
            "Declare these in the registry with scoped=True, so they are typed "
            "and checked against the rest like any other, and switch them on "
            "from the handler that builds the page with shortcuts.use(). It "
            "works the way toast.success() does. There is nothing to pass "
            "along, because the router opens and closes the request's list, "
            "and HueRequestMiddleware does the same for a plain Django view."
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
            "The latest response decides which scoped shortcuts are on. For an "
            "app that has any, every fragment response brings a fresh copy of "
            "the page's bindings, which replaces the old one: a handler that "
            "swaps in another invoice calls use() again, and the archive key "
            "archives the invoice now on screen, while one that calls nothing "
            "turns the shortcut off, so a key never acts on content that has "
            "been swapped away. Calling use() outside a request raises an "
            "error."
        ),
        pr.h2("While someone is typing"),
        pr.p(
            "In a text field, a Select, a Combobox, a menu or anything "
            "editable, only a shortcut with mod or ctrl in it runs, since a "
            "letter there types or jumps to an option. Otherwise typing the "
            'word "gb" into a comment box would leave the page, and alt is no '
            "exception, "
            'since Option-C types "ç" on a Mac. That is why a palette\'s '
            "hotkey normally uses mod. Keys pressed while an input method is "
            "composing a character are ignored as well."
        ),
        pr.h2("While a dialog is open"),
        pr.p(
            "Nothing outside an open modal dialog runs, since it would act on "
            "the page underneath. The command palette is the exception, being "
            "a modal whose job is to list the shortcuts. Its search field has "
            "focus while it is open, so the rule for typing applies: a "
            "shortcut with mod or ctrl still runs, the palette's own hotkey "
            "included, which closes it."
        ),
        pr.h2("Letting people switch them off"),
        pr.p(
            "Single-key shortcuts are a problem for people who use speech "
            "input, where a spoken word arrives as a string of key presses, and "
            "for anyone who presses keys by accident. WCAG 2.1.4 (Character Key "
            "Shortcuts) requires that shortcuts like these can be turned off. "
            "Hue keeps that setting in an Alpine store, $store.shortcuts.letters, "
            "and remembers it in the browser. Shortcuts with mod, ctrl or alt "
            "are not affected."
        ),
        pr.p(
            "Put a switch for it in your app's settings. It needs nothing but "
            "the binding:"
        ),
        pr.code(
            "(\n"
            '    Switch().name("letter_shortcuts")\n'
            '    .label("Single-key shortcuts")\n'
            '    .description("Such as G then B to go to Billing.")\n'
            '    .x_model("$store.shortcuts.letters")\n'
            ")"
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
        pr.h2("Keys that are only shown"),
        pr.p(
            "Tooltip's keys() takes a Kbd and binds nothing, because it "
            "describes the key of the control it sits on. Bind the key in the "
            "registry, or as a palette's hotkey, and let the tooltip say what "
            "it is.",
        ),
        pr.code('Tooltip().content("Search").keys(Kbd("mod", "K"))'),
    )


PAGE = ProsePage(
    slug="keyboard-shortcuts",
    title="Keyboard shortcuts",
    nav_label="Keyboard shortcuts",
    group="Guides",
    order=5,
    build=_build,
)
