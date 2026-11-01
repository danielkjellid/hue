from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert

from hue_docs.layout import prose as pr
from hue_docs.model import GuidePage


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
            "No amount of escaping makes code safe, so `on_click()`, `x_on()` "
            "and the `x_` directives that evaluate their argument do not take "
            "a string. They take an `Expression`, a `str` subclass whose type "
            "says that somebody built it on purpose. Passing a plain string "
            "raises a `TypeError` that points at the helpers below. One "
            "exception remains for now: `x_data()` takes a dict, which is "
            "quoted, or a string, which is written as it is. Treat a string "
            "given to it as `unsafe()`. Alpine AJAX's events have modifiers of "
            "their own, such as `ajax_success()`, and take an expression the "
            "same way."
        ),
        pr.bullets(
            [
                "`call()` calls a function on the page, quoting its arguments.",
                "`ajax()` sends a request to one of your routes and merges the "
                "response into the page.",
                "`close()` closes the `Dialog`, `Drawer`, `Popover` or "
                "`DropdownMenu` the control sits in.",
                "`toast.js` raises a toast in the browser.",
                "`unsafe()` vouches for source you wrote yourself, and is the "
                "only way to turn your own text into an `Expression`.",
            ]
        ),
        pr.p(
            "An action goes to `on_click()` on the components a browser "
            "already treats as a control: `Button`, `MenuItem`, "
            "`SegmentedOption` and `SidebarItem`. Pass several and they run in "
            "order. A toast's action takes one too, and `x_on()` attaches one "
            "to any event on anything else."
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
            "`call()` writes a call to a function the page already has: one "
            "of your own scripts, a method on an Alpine store, `window.print`. "
            "Its arguments are quoted as JSON, so a string with an apostrophe "
            "in it stays a string, and anything a dict can hold can be passed."
        ),
        pr.code(
            'call("sendInvoice", 2048)  # sendInvoice(2048)\n'
            'call("greet", "O\'Hara")  # greet("O\'Hara")\n'
            'call("$store.cart.add", 7)  # $store.cart.add(7)'
        ),
        pr.p(
            "The function has to be a name or a path to one. Anything else "
            "raises a `ValueError`, because there would be nothing left for "
            "`call()` to quote."
        ),
        pr.h2("ajax()"),
        pr.p(
            "`ajax()` writes Alpine AJAX's `$ajax`: a request to the URL you "
            "give it, whose response fills the elements you name. It is how a "
            "button, a menu item or a toast reaches a route without a form "
            "around it."
        ),
        pr.code(
            "from hue.js import ajax\n\n"
            "ajax(\n"
            '    "/invoices/2048/archive/",\n'
            '    method="post",\n'
            '    target="invoice",\n'
            '    body=Archive(reason="duplicate"),\n'
            ")\n"
            '# $ajax("/invoices/2048/archive/", {"method": "post",\n'
            '#        "target": "invoice", "sync": true,\n'
            '#        "body": {"reason": "duplicate", "notify": false}})'
        ),
        pr.bullets(
            [
                "`target` is the id of the element the response fills, or a "
                "list of ids for several. It is required, because without it "
                "`$ajax` would use the id of whatever ran it, and fail on an "
                "element without one.",
                "`method` is `get`, `post`, `put`, `patch` or `delete`, and "
                "defaults to `get`, as `$ajax`'s own does. Use the method the "
                "route was declared with: `fragment_delete` answers `delete`.",
                "`body` is an instance of the type the route declares for its "
                "`body` parameter, a dataclass or a pydantic model, and its "
                "fields are sent as a form would send them. A field whose "
                "value is `None` is left out, so the route's default applies. "
                "A GET takes no body: `$ajax` would send it as the query "
                "string, which a body model never reads, so `ajax()` refuses "
                "it and its values go in the URL.",
            ]
        ),
        pr.p(
            "The response is merged by id. For each target, the element in "
            "the response with that id gives its contents to the element with "
            "that id on the page, which keeps its own attributes and classes. "
            "A route returns a component whose outermost element has that id, "
            "or wraps one in `HueResponse(target=...)`, which adds it. A "
            "successful response that does not contain a target removes it "
            "from the page, so an id the route gets wrong makes the element "
            "disappear."
        ),
        pr.p(
            "The CSRF token needs nothing from you. Hue's bundle sends it as "
            "the `X-CSRFToken` header on every request Alpine AJAX makes, and "
            "both `hue-django` and `hue-fastapi` read it from there. Toasts "
            "raised by the route arrive with the response, as they do for a "
            "form. The toast region is synced, and `ajax()` asks for synced "
            "elements to be updated too, which is the `sync: true` in its "
            "output. A synced element the response does not contain, such as "
            "a table elsewhere on the page, is left as it is."
        ),
        pr.h2("Parameters in the URL"),
        pr.p(
            "A route needs to know what to act on, and where that comes from "
            "depends on when it is known. Most parameters are known on the "
            "server, such as the invoice a page shows. Put them in the URL, "
            "the way the route's path declares them, and build the URL from "
            "the route's name while rendering, so it is right wherever the "
            "view is mounted. A route is named after its handler and a view's "
            "URLs after its class, both in lower case, so the delete route "
            'below is `"invoices:delete"`. Django builds the URL with '
            '`reverse("invoices:delete", kwargs={"id": 7})` and FastAPI with '
            '`request.url_for("invoices:delete", id=7)`.'
        ),
        pr.code(
            "class Invoices(HueView):\n"
            "    router = Router[HttpRequest]()\n\n"
            '    @router.fragment_delete("<int:id>/")\n'
            "    async def delete(self, request, context, id: int):\n"
            "        await delete_invoice(id)\n"
            '        toast.success("Invoice deleted")\n'
            "        return InvoiceList()\n\n\n"
            "# in whatever renders the invoice, here with Django's reverse()\n"
            'Button().content("Delete").variant("danger").on_click(\n'
            "    ajax(\n"
            '        reverse("invoices:delete", kwargs={"id": invoice.id}),\n'
            '        method="delete",\n'
            '        target="invoices",\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "The path above uses Django's `<int:id>` syntax. With "
            "`hue-fastapi` the same route is `{id}`, and the handler's `id: "
            "int` annotation does the converting."
        ),
        pr.h2("Parameters in the body"),
        pr.p(
            "Values that are not part of the address, such as a reason or a "
            "flag, go in the body. The route declares a `body` parameter with "
            "a type, and hue validates the fields against it, answering 422 "
            "when they do not fit. Pass an instance of that same type to "
            "`ajax()`, so the request and the route cannot drift apart."
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
            '    body=Archive(reason="duplicate", notify=True),\n'
            ")"
        ),
        pr.p(
            "A pydantic model works the same way, in the route and in "
            "`ajax()`. A list or a dict in the body arrives as one field "
            "holding JSON, the way `$ajax` sends them, so the route reads "
            '`[3, 4]` from the text `"[3,4]"`. Declare that field with '
            "pydantic's `Json` type and it is parsed for you:"
        ),
        pr.code(
            "from pydantic import Json\n\n\n"
            "@dataclass\n"
            "class ArchiveMany:\n"
            "    ids: Json[list[int]]\n"
            '    note: str = ""'
        ),
        pr.p(
            "A form sends a list differently. Checkboxes that share a name, "
            "or a `Combobox` that takes several choices, send that name once "
            "for each value. Declare the field as a `list`, a `tuple` or a "
            "`set` and it receives every one of them. Any other field "
            "receives the last value sent under its name. ",
            pr.link("Forms", "/forms/"),
            " covers posting a whole form.",
        ),
        pr.h2("Values only the browser has"),
        pr.p(
            "Some values exist only in the page: the rows ticked, what is "
            "typed in a field. Pass those as an expression, which goes in as "
            "written while everything around it is still quoted, however deep "
            "in the body it sits. This is the same rule `call()` follows. A "
            "dataclass takes an expression in any field. A pydantic model "
            "would reject one for a `list[int]`, so build that body with "
            "`model_construct()`, which skips validation."
        ),
        pr.code(
            "from hue.js import ajax, unsafe\n\n"
            "ajax(\n"
            '    "/invoices/archive/",\n'
            '    method="post",\n'
            '    target=["invoices-rows", "invoices-summary"],\n'
            "    body=ArchiveMany(\n"
            '        ids=unsafe("selected"),\n'
            '        note=unsafe("$refs.note.value"),\n'
            "    ),\n"
            ")\n"
            '# "body": {"ids": selected, "note": $refs.note.value}'
        ),
        pr.p(
            "The URL can be an expression too, for a path the browser builds, "
            "though a URL built from the route's name on the server is the "
            "better habit, since it follows the view wherever it is mounted."
        ),
        pr.h2("unsafe()"),
        pr.p(
            "`unsafe()` is for a short piece of state you wrote yourself, such "
            "as `open = !open`, and for a value only the browser has, such as "
            "`selected`. Because it is spelled the same way everywhere, one "
            "grep for `unsafe(` finds every place that decision was made."
        ),
        Alert()
        .variant("warning")
        .title("Never build unsafe() out of user input")
        .content(
            pr.rich(
                "Anything inside `unsafe()` runs as code in the reader's "
                "browser. A value someone typed belongs in `call()` or "
                "`ajax()`, as an argument or a body field, where it is quoted "
                "and stays a value. The protection covers hue's own "
                "modifiers. An expression written straight into an htmy "
                'attribute, such as `html.button(**{"@click": ...})`, goes '
                "around it, as does anything a template renders itself."
            )
        ),
    )


PAGE = GuidePage(
    slug="actions",
    title="Actions and requests",
    nav_label="Actions and requests",
    group="Guides",
    order=1,
    build=_build,
)
