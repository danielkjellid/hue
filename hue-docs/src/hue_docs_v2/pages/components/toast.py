from __future__ import annotations

from fastapi import Request
from hue import html, toast
from hue.context import HueContext
from hue.js import ajax
from hue.types.core import ComponentType
from hue.ui import Alert, Button, Stack, Text, Toast, ToastRegion
from hue_fastapi import HueFragmentsView, Router

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel


class ToastDemo(HueFragmentsView):
    """
    The route behind the server-raised example: it raises a toast and returns
    a line of status, and the router carries the toast along behind it.
    """

    router = Router[Request]()

    @router.fragment_post("send/")
    async def send(
        self, request: Request, context: HueContext[Request]
    ) -> ComponentType:
        toast.success("Invoice sent", description="INV-2048 to ada@example.com")
        return (
            html.p("Sent just now.").id("send-status").class_("text-sm text-fg-muted")
        )


# From the server


def raised_by_a_route() -> ComponentType:
    return Stack().content(
        Button()
        .content("Send invoice")
        .on_click(ajax("/demos/toast/send/", method="post", target="send-status")),
        html.p("Not sent yet.").id("send-status").class_("text-sm text-fg-muted"),
    )


# From the browser


def raise_success() -> Button:
    return (
        Button()
        .variant("outline")
        .content("Success")
        .on_click(toast.js.success("Invoice sent", description="INV-2048 to Ada"))
    )


def raise_danger() -> Button:
    return (
        Button()
        .variant("outline")
        .content("Danger")
        .on_click(toast.js.danger("Could not send", description="The address bounced."))
    )


def raise_warning() -> Button:
    return (
        Button()
        .variant("outline")
        .content("Warning")
        .on_click(toast.js.warning("Sent without the PDF"))
    )


def raise_info() -> Button:
    return (
        Button()
        .variant("outline")
        .content("Info")
        .on_click(toast.js.info("Back online"))
    )


def raise_loading() -> Button:
    return (
        Button()
        .variant("outline")
        .content("Loading")
        .on_click(toast.js.loading("Exporting 2,481 rows", duration=None))
    )


# Variants, as specimens: a Toast outside a region has no timer and stays.


def success() -> Toast:
    return (
        Toast().variant("success").title("Invoice sent").description("INV-2048 to Ada")
    )


def danger() -> Toast:
    return (
        Toast()
        .variant("danger")
        .title("Could not send")
        .description("The address bounced.")
    )


def warning() -> Toast:
    return Toast().variant("warning").title("Sent without the PDF")


def info() -> Toast:
    return Toast().variant("info").title("Back online")


def loading() -> Toast:
    return Toast().variant("loading").title("Exporting 2,481 rows").dismissible(False)


# Anatomy


def title_only() -> Toast:
    return Toast().variant("success").title("Saved")


def with_description() -> Toast:
    return (
        Toast().variant("success").title("Saved").description("Three fields changed.")
    )


def with_action() -> Toast:
    return (
        Toast()
        .variant("danger")
        .title("Could not send invoice")
        .description("The mail server rejected the address.")
        .action(Button().variant("ghost").size("xs").content("Retry"))
    )


def not_dismissible() -> Toast:
    return Toast().variant("loading").title("Uploading").dismissible(False)


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Put the region in your page base"),
        pr.p(
            "`ToastRegion` collects toasts, announces them and times them. It "
            "has the fixed id `hue-toasts`, which the toasts behind a fragment "
            "are merged into, so a page holds exactly one. Put it in your page "
            "base."
        ),
        pr.code(
            "from hue.ui import ToastRegion\n\n"
            "def index(request, context):\n"
            "    return Page(\n"
            '        title="Invoices",\n'
            "        body=html.div(invoices_table(), ToastRegion()),\n"
            "    )"
        ),
        pr.p(
            "When the request that drew the page queued no toast, the region "
            "renders empty. A live region created together with its content is "
            "never read out, so it has to be on the page before a toast arrives "
            "over AJAX."
        ),
        pr.h2("Raise one from a route"),
        pr.p(
            "`toast.success()` queues a toast for the current request. You pass "
            "no context and no target, because whatever the route returns "
            "carries it. "
            "A page renders it into its own region. A fragment gets the region "
            "appended behind it, and Alpine AJAX merges that into the region on "
            "the page, because the region carries `x-sync` and so is a target of "
            "every request the page makes."
        ),
        pr.code(
            "from hue import toast\n\n"
            '@router.fragment_post("invoices/{id}/send/")\n'
            "async def send(self, request, context, id: int):\n"
            "    await send_invoice(id)\n"
            "    toast.success(\n"
            '        "Invoice sent", description="INV-2048 to ada@example.com"\n'
            "    )\n"
            "    return InvoiceRow(id)"
        ),
        pr.p(
            "The route path is written in FastAPI's syntax. In `hue-django` "
            "the same route is `invoices/<int:id>/send/`."
        ),
        pr.p(
            "There is one method per variant, with the options `description`, "
            "`duration`, `dismissible` and `action`. The queue lives exactly as "
            "long as the request, so a toast cannot surface in somebody else's "
            "response. Calling `toast.success()` outside a request raises a "
            "`RuntimeError` instead of dropping the toast."
        ),
        pr.h3("Across a redirect"),
        pr.p(
            "A redirect has no markup to carry a toast. `HueRequestMiddleware`, "
            "which `hue-django` and `hue-fastapi` each provide, keeps such "
            "toasts in the session and hands them to the next page. Without "
            "the middleware, a hue route that raises a toast and then "
            "redirects raises a `RuntimeError` instead of dropping it. An action "
            "cannot cross a redirect, because an action is a component rather "
            "than data."
        ),
        pr.p(
            "In Django, list hue's middleware after Django's "
            "`SessionMiddleware` in `MIDDLEWARE`:"
        ),
        pr.code(
            "# settings.py\n"
            "MIDDLEWARE = [\n"
            '    "django.contrib.sessions.middleware.SessionMiddleware",\n'
            '    "hue_django.middleware.HueRequestMiddleware",\n'
            "    ...\n"
            "]"
        ),
        pr.p(
            "In FastAPI, add `HueRequestMiddleware` first and Starlette's "
            "`SessionMiddleware` after it. Starlette runs the middleware added "
            "last first, so the session wraps hue's middleware:"
        ),
        pr.code(
            "from hue_fastapi import HueRequestMiddleware\n"
            "from starlette.middleware.sessions import SessionMiddleware\n\n"
            "app.add_middleware(HueRequestMiddleware)\n"
            "app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)"
        ),
        pr.h2("Raise one from the browser"),
        pr.p(
            "For something the server never hears about, such as a copy to the "
            "clipboard, `toast.js` builds the expression to hand to `on_click()`. The "
            "values are quoted for you, so an apostrophe in a description is a "
            "word and not a syntax error. `duration` is in milliseconds, `None` "
            "keeps the toast until it is dismissed, and leaving it out takes the "
            "region's default. `action` is a pair of a label and the expression "
            "its button runs."
        ),
        pr.code(
            "from hue import toast\n"
            "from hue.js import ajax\n\n"
            'Button().content("Copy link").on_click(\n'
            '    toast.js.success("Copied to clipboard")\n'
            ")\n\n"
            "toast.js.danger(\n"
            '    "Could not send invoice",\n'
            '    description="The mail server rejected the address.",\n'
            "    action=(\n"
            '        "Retry",\n'
            '        ajax("/invoices/2048/send/", method="post", target="invoice"),\n'
            "    ),\n"
            ")"
        ),
        Alert()
        .variant("warning")
        .title("What is safe to interpolate")
        .content(
            pr.rich(
                "Titles, descriptions and action labels are quoted and written "
                "into the page as text, so building them from user input is "
                "safe. The second half of an action is code, so it has to be an "
                "expression built with `ajax()`, `call()` or `unsafe()`; a plain "
                "string is refused. Never build one with `unsafe()` from user "
                "input. The region also accepts toasts from any response that "
                "carries its id, so fetch fragments only from your own app."
            )
        ),
        pr.p(
            "`toast.js` produces a call to the `$toast` magic, which any Alpine "
            "expression can also call directly. The markup is cloned from "
            "templates the region renders, so a toast raised in the browser is "
            "the same element as one rendered in Python. With no region on the "
            "page, `$toast` logs a warning to the console and drops the message."
        ),
        pr.code(
            "$toast.success('Invoice sent', { description: 'INV-2048 to Ada' })\n"
            "$toast.loading('Exporting 2,481 rows', { duration: null })",
            language="javascript",
        ),
        pr.h2("How long a toast stays"),
        pr.p(
            "A toast stays for 5200 milliseconds by default. The region does "
            "the timing, so a `Toast` rendered on its own, like the specimens "
            "on this page, has no timer and stays. Set the page-wide default "
            "with `default_duration()` on the region, and override it per toast."
        ),
        pr.code(
            "ToastRegion().default_duration(8000)\n\n"
            'Toast().variant("info").title("Back online").duration(2000)\n'
            'Toast().variant("loading").title("Exporting").duration(None)'
        ),
        pr.p(
            "The timer pauses while a pointer is over the toast or focus is "
            "inside it, and restarts at 2600ms when they leave. WCAG 2.2.1 "
            "requires that a message which leaves on its own can be paused by "
            "whoever is still reading it."
        ),
        pr.h2("Toast variants"),
        pr.p(
            'A toast\'s variant sets its icon and colour: `"success"`, `"danger"`, '
            '`"warning"`, `"info"` or `"loading"`. A danger toast is also copied into '
            'a `role="alert"` element and read at once. A loading toast shows a '
            "spinner in place of the icon. `duration(None)` keeps any toast on screen "
            "until it is dismissed, and `dismissible(False)` leaves out its close "
            "button."
        ),
    )


PAGE = ComponentPage(
    Toast,
    lede=(
        "A toast is a short note about something that just happened. It "
        "arrives in one corner, is read out politely, and leaves on its own. "
        "Raise one from a route or from the browser; the region on the page "
        "shows it either way."
    ),
    usage=_usage,
    panels=[
        panel(
            "From the server",
            raised_by_a_route,
            layout="stack",
            min_height=240,
            hint="A POST to a route that raises it",
        ),
        panel(
            "From the browser",
            raise_success,
            raise_danger,
            raise_warning,
            raise_info,
            raise_loading,
            min_height=280,
            captions=False,
            hint="`toast.js`, no request",
        ),
        panel(
            "Variants",
            success,
            danger,
            warning,
            info,
            loading,
            layout="stack",
        ),
        panel(
            "Anatomy",
            title_only,
            with_description,
            with_action,
            not_dismissible,
            layout="stack",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The region is an `aria-live="polite"` container, so a toast is '
            "read at the next pause. A danger toast is also copied into a "
            'separate, always-present `role="alert"` element, so a failure is '
            "read at once.",
        ),
        Note(
            "a11y",
            "Nothing moves focus. A keyboard user reaches the dismiss button and "
            "any action by tabbing to them, as with anything else on the page.",
        ),
        Note(
            "a11y",
            "The timer pauses on hover and on focus, which WCAG 2.2.1 requires of "
            "content that disappears on its own.",
        ),
        Note(
            "note",
            "A toast leaves the screen once its duration is up. An `Alert` stays "
            "until it is dismissed.",
        ),
    ],
    parts=[ToastRegion],
    related=[Alert, Text],
    views=[ToastDemo],
)
