from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Actions and requests"),
        pr.lead(
            "What a control does when it is pressed is code the browser runs. "
            "Hue builds that code for you from Python values, quoting each "
            "one, so the short way to write an action is also the safe one."
        ),
        pr.h2("Expressions"),
        pr.p(
            "No amount of escaping makes code safe, so on_click(), x_on() and "
            "the x_ directives that evaluate their argument do not take a "
            "string. They take an Expression, a str "
            "subclass whose type says that somebody built it on purpose. "
            "Passing a plain string raises a TypeError that points at the "
            "helpers below. Two exceptions remain for now: x_data() takes a "
            "dict, which is quoted, or a string, which is written as it is, "
            "and the ajax_ event handlers, such as ajax_success(), take a "
            "string as written. Treat a string given to either as unsafe()."
        ),
        pr.bullets(
            [
                pr.p("call() calls a function on the page, quoting its arguments."),
                pr.p(
                    "ajax() sends a request to one of your routes and merges "
                    "the response into the page."
                ),
                pr.p(
                    "close() closes the Dialog, Drawer, Popover or "
                    "DropdownMenu the control sits in."
                ),
                pr.p("toast.js raises a toast in the browser."),
                pr.p(
                    "unsafe() vouches for source you wrote yourself, and is "
                    "the only way to turn your own text into an Expression."
                ),
            ]
        ),
        pr.p(
            "An action goes to on_click() on the components a browser already "
            "treats as a control: Button, MenuItem, SegmentedOption and "
            "SidebarItem. Pass several and they run in order. A toast's "
            "action takes one too, and x_on() "
            "attaches one to any event on anything else."
        ),
        pr.code(
            "from hue.js import ajax, call, close\n\n"
            'Button().content("Send").on_click(call("sendInvoice", invoice.id))\n\n'
            'Button().content("Save").on_click(\n'
            '    ajax("/invoices/2048/", method="post", target="invoice"),\n'
            "    close(),\n"
            ")"
        ),
        pr.h2("call()"),
        pr.p(
            "call() writes a call to a function the page already has: one of "
            "your own scripts, a method on an Alpine store, window.print. Its "
            "arguments are quoted as JSON, so a string with an apostrophe in "
            "it stays a string, and anything a dict can hold can be passed."
        ),
        pr.code(
            'call("sendInvoice", 2048)  # sendInvoice(2048)\n'
            'call("greet", "O\'Hara")  # greet("O\'Hara")\n'
            'call("$store.cart.add", 7)  # $store.cart.add(7)'
        ),
        pr.p(
            "The function has to be a name or a path to one. Anything else "
            "raises a ValueError, because there would be nothing left for "
            "call() to quote."
        ),
        pr.h2("ajax()"),
        pr.p(
            "ajax() writes Alpine AJAX's $ajax: a request to the URL you give "
            "it, whose response fills the elements you name. It is how a "
            "button, a menu item or a toast reaches a route without a form "
            "around it."
        ),
        pr.code(
            "from hue.js import ajax\n\n"
            "ajax(\n"
            '    "/invoices/2048/archive/",\n'
            '    method="post",\n'
            '    target="invoice",\n'
            '    body={"reason": "duplicate"},\n'
            ")\n"
            '# $ajax("/invoices/2048/archive/", {method: "post", target: "invoice",\n'
            '#        sync: true, body: {"reason": "duplicate"}})'
        ),
        pr.bullets(
            [
                pr.p(
                    "target is the id of the element the response fills, or a "
                    "list of ids for several. It is required: left out, "
                    "$ajax would use the id of whatever ran it, and fail on "
                    "an element without one."
                ),
                pr.p(
                    "method is get, post, put, patch or delete, and defaults "
                    "to get, as $ajax's own does. Use the method the route "
                    "was declared with: fragment_delete answers delete."
                ),
                pr.p(
                    "body is a dict of fields, sent as a form would send "
                    "them. A field whose value is None is left out, so the "
                    "route's default applies. A GET takes no body: $ajax "
                    "would send it as the query string, which a body model "
                    "never reads, so ajax() refuses it and its values go in "
                    "the URL."
                ),
            ]
        ),
        pr.p(
            "The response is merged by id. For each target, the element in "
            "the response with that id gives its contents to the element with "
            "that id on the page, which keeps its own attributes and classes. "
            "A route returns a component whose outermost element has that id, "
            "or wraps one in HueResponse(target=...), which adds it. A "
            "successful response that does not contain a target removes it "
            "from the page, so an id the route gets wrong makes the element "
            "disappear."
        ),
        pr.p(
            "The CSRF token needs nothing from you. Hue's bundle sends it as "
            "the X-CSRFToken header on every request Alpine AJAX makes, which "
            "is the header Django reads. Toasts raised by the route arrive "
            "with the response, as they do for a form: the toast region is "
            "synced, and ajax() asks for synced elements to be updated too; "
            "that is the sync: true in its output. A synced element the "
            "response does not contain, a table elsewhere on the page say, "
            "is left as it is."
        ),
        pr.h2("Known on the server, in the address: the URL"),
        pr.p(
            "A route needs to know what to act on, and where that comes from "
            "depends on when it is known. "
            "Most parameters are known on the server, such as the invoice a "
            "page shows. Put them in the URL, the way the route's path "
            "declares them, and reverse it while rendering, so the URL is "
            "right wherever the view is mounted. A route is named after its "
            "handler and a view's URLs after its class, both in lower case, "
            'so the delete route below is "invoices:delete".'
        ),
        pr.code(
            "class Invoices(HueView):\n"
            "    router = Router[HttpRequest]()\n\n"
            '    @router.fragment_delete("<int:id>/")\n'
            "    async def delete(self, request, context, id: int):\n"
            "        await delete_invoice(id)\n"
            '        toast.success("Invoice deleted")\n'
            "        return InvoiceList()\n\n\n"
            "# in whatever renders the invoice\n"
            'Button().content("Delete").variant("danger").on_click(\n'
            "    ajax(\n"
            '        reverse("invoices:delete", kwargs={"id": invoice.id}),\n'
            '        method="delete",\n'
            '        target="invoices",\n'
            "    )\n"
            ")"
        ),
        pr.h2("Known on the server, outside the address: the body"),
        pr.p(
            "Values that are not part of the address, such as a reason or a "
            "flag, go in body. The route declares a body parameter with a "
            "type, and hue validates the fields against it, answering 422 "
            "when they do not fit."
        ),
        pr.code(
            "@dataclass\n"
            "class Archive:\n"
            "    reason: str\n"
            "    notify: bool = False\n\n\n"
            '@router.fragment_post("<int:id>/archive/")\n'
            "async def archive(self, request, context, id: int, body: Archive):\n"
            "    ...\n\n\n"
            "ajax(\n"
            '    reverse("invoices:archive", kwargs={"id": invoice.id}),\n'
            '    method="post",\n'
            '    target="invoice",\n'
            '    body={"reason": "duplicate", "notify": True},\n'
            ")"
        ),
        pr.p(
            "A list or a dict in the body arrives as one field holding JSON, "
            "the way $ajax sends them, so the route reads [3, 4] from the "
            'text "[3,4]". Declare that field with pydantic\'s Json type and '
            "it is parsed for you:"
        ),
        pr.code(
            "from pydantic import Json\n\n\n"
            "@dataclass\n"
            "class ArchiveMany:\n"
            "    ids: Json[list[int]]"
        ),
        pr.p(
            "A form sends a list differently. Checkboxes that share a name, "
            "or a Combobox that takes several choices, send that name once "
            "for each value. Declare the field as a list, a tuple or a set "
            "and it receives every one of them. Any other field receives the "
            "last value sent under its name."
        ),
        pr.h2("Known only in the browser: an expression"),
        pr.p(
            "Some values exist only in the page: the rows ticked, what is "
            "typed in a field. Pass those as an expression, which goes in as "
            "written while everything around it is still quoted. This is the "
            "same rule call() follows."
        ),
        pr.code(
            "from hue.js import ajax, unsafe\n\n"
            "ajax(\n"
            '    "/invoices/archive/",\n'
            '    method="post",\n'
            '    target=["invoices-rows", "invoices-summary"],\n'
            "    body={\n"
            '        "ids": unsafe("selected"),\n'
            '        "note": unsafe("$refs.note.value"),\n'
            "    },\n"
            ")\n"
            '# body: {"ids": selected, "note": $refs.note.value}'
        ),
        pr.p(
            "The URL can be an expression too, for a path the browser "
            "builds, though a URL reversed on the server is the better habit: "
            "it follows the view wherever it is mounted."
        ),
        pr.h2("unsafe()"),
        pr.p(
            "unsafe() is for a short piece of state you wrote yourself, such "
            "as open = !open, and for a value only the browser has, such as "
            "selected. Its name is the whole mechanism: every place that "
            "decision was made answers to one grep."
        ),
        Alert()
        .variant("warning")
        .title("Never build unsafe() out of user input")
        .content(
            pr.p(
                "Anything inside unsafe() runs as code in the reader's "
                "browser. A value someone typed belongs in call() or "
                "ajax(), as an argument or a body field, where it is quoted "
                "and stays a value. The protection covers hue's own "
                "modifiers: an expression written straight into an htmy "
                'attribute, such as html.button(**{"@click": ...}), goes '
                "around it, as does anything a template renders itself."
            )
        ),
    )


PAGE = ProsePage(
    slug="actions",
    title="Actions and requests",
    nav_label="Actions and requests",
    group="Guides",
    order=1,
    build=_build,
)
