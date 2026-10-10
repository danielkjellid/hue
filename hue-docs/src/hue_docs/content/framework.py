from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Framework concepts"),
        pr.lead(
            "A short tour of the ideas behind Hue. These are deliberately "
            "high-level, and each maps to a module you can read in the repository."
        ),
        pr.h2("Chainable components"),
        pr.p(
            "Every component extends ChainableComponent. Modifier methods like "
            ".variant() or .class_() set properties and return self, so calls "
            "chain. Children are passed positionally or via .content(). The "
            "concrete markup is produced by the component's _render method."
        ),
        pr.h2("Context and rendering"),
        pr.p(
            "Rendering is async. render_tree wraps your components in a "
            "HueContext that carries the request and CSRF token, then hands the "
            "tree to htmy's renderer. Components read what they need from the "
            "context during render."
        ),
        pr.p(
            "The context is open: a component can offer values of its own to "
            "everything rendered inside it, which is how a sidebar tells its "
            "links which page they are on and a form tells its controls what "
            "is wrong with them. See ",
            pr.link("Contexts", "/contexts/"),
            " for the contract and when to reach for it.",
        ),
        pr.h2("Router and Alpine AJAX"),
        pr.p(
            "Hue is AJAX-first. A framework-agnostic Router registers routes "
            "that return HTML fragments; on the client, Alpine AJAX swaps those "
            "fragments into the DOM. Components expose helpers such as "
            ".x_on() and the .ajax_* handlers to drive these interactions."
        ),
        pr.p(
            "Because this documentation site is static, those live AJAX "
            "exchanges aren't wired to a backend here, so interactive examples "
            "are shown as code."
        ),
        pr.h2("Expressions"),
        pr.p(
            "What a control does when pressed is code, so the modifiers that "
            "run it take an Expression rather than a string. ",
            pr.link("Actions and requests", "/actions/"),
            " covers the helpers that build one, sending a request to a "
            "route, and passing it parameters.",
        ),
        pr.code(
            "from hue.js import ajax, call\n\n"
            'Button().content("Send").on_click(call("sendInvoice", invoice.id))\n'
            'Button().content("Delete").on_click(\n'
            "    ajax(\n"
            '        reverse("invoices:delete", kwargs={"id": invoice.id}),\n'
            '        method="delete",\n'
            '        target="invoices",\n'
            "    )\n"
            ")"
        ),
        pr.h2("Static assets"),
        pr.p(
            "The Tailwind stylesheet and Alpine bundle live inside the hue "
            "package and are exposed through hue.assets. Framework integrations "
            "serve them; the theme is defined as Tailwind v4 @theme tokens you "
            "can extend."
        ),
        pr.h2("Theming"),
        pr.p(
            "Colour and dark mode are driven by CSS variables and a "
            "data-theme attribute on the document. Toggle the switch in the "
            "top bar to see every component respond to the dark theme."
        ),
    )


PAGE = ProsePage(
    slug="framework",
    title="Framework concepts",
    nav_label="Framework concepts",
    group="Guides",
    order=0,
    build=_build,
)
