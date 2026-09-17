from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Toasts"),
        pr.lead(
            "A toast is a transient note about something that just happened. "
            "It arrives in one corner, reads out politely, and leaves on its "
            "own. Nothing in a toast is the only way to do anything: if the "
            "user has to act, that belongs in an Alert that stays."
        ),
        pr.h2("Put the region in your page base"),
        pr.p(
            "ToastRegion is the thing that collects toasts, announces them "
            "and times them. It goes in your page base once, so every page "
            "has exactly one and toasts always arrive in the same corner - "
            "moving them between screens destroys the reflex to look there."
        ),
        pr.code(
            "from hue.pages import create_page_base\n"
            "from hue.ui import ToastRegion\n\n"
            "Page = create_page_base(\n"
            '    css_url="/static/hue/styles.css",\n'
            '    js_url="/static/hue/js/alpine.js",\n'
            ")\n\n"
            "def index(request, context):\n"
            "    return Page(\n"
            '        title="Invoices",\n'
            "        body=html.div(\n"
            "            invoices_table(),\n"
            "            ToastRegion(),\n"
            "        ),\n"
            "    )"
        ),
        pr.p(
            "The region renders empty and stays empty until something is put "
            "in it. That is deliberate: a live region created together with "
            "its content is never read out, so it has to be on the page "
            "before the first toast arrives."
        ),
        pr.h2("Raise one from the browser"),
        pr.p(
            "$toast is available in any Alpine expression. Use it for things "
            "the server never hears about - a copy to the clipboard, going "
            "offline, a confirmation that costs nothing to produce - where a "
            "round trip would exist only to make a sentence appear."
        ),
        pr.code(
            "from hue.ui import Button\n\n"
            "(\n"
            '    Button().content("Copy link")\n'
            "    .x_on(\n"
            '        "click",\n'
            '        "navigator.clipboard.writeText($el.dataset.url); "\n'
            "        \"$toast.success('Copied to clipboard')\",\n"
            "    )\n"
            ")"
        ),
        pr.p(
            "There is one function per variant - success, danger, warning, "
            "info and loading - each taking a title and an options object:"
        ),
        pr.code(
            "$toast.success('Invoice sent', {\n"
            "    description: 'INV-2048 sent to ada@example.com',\n"
            "})\n\n"
            "// stays until it is dismissed\n"
            "$toast.loading('Exporting 2,481 rows', { duration: null })\n\n"
            "// or a number of milliseconds of its own\n"
            "$toast.info('Back online', { duration: 2000 })",
            language="javascript",
        ),
        pr.p(
            "The markup is cloned from templates the region renders, not "
            "written in JavaScript, so a toast raised in the browser is the "
            "same element as one rendered by Python - same classes, same "
            "timer, same dismiss button. If there is no region on the page, "
            "$toast warns in the console and drops the message rather than "
            "failing silently."
        ),
        pr.h2("How long they stay"),
        pr.p(
            "5200 milliseconds by default, which is about as long as it "
            "takes to read two short lines twice. Set the page-wide number "
            "on the region, and override it on a toast that needs longer or "
            "should not leave at all:"
        ),
        pr.code(
            "ToastRegion().duration(8000)\n\n"
            'Toast().variant("info").title("Back online").duration(2000)\n'
            'Toast().variant("loading").title("Exporting").duration(None)'
        ),
        pr.p(
            "The timer stops while a pointer is over the toast or focus is "
            "inside it, and restarts at 2600ms when they leave - shorter, "
            "because by then the toast has already been on screen. WCAG "
            "2.2.1 requires this: a message that leaves on its own has to be "
            "stoppable by whoever is still reading it."
        ),
        pr.h2("What each variant is for"),
        pr.p(
            "success confirms something that finished, danger reports "
            "something that failed, warning flags something that went "
            "through with a caveat, info says something the user did not ask "
            "about, and loading is a pending state with a spinner instead of "
            "an icon. A loading toast usually sets duration(None) and "
            "dismissible(False), since what ends it is the thing it is "
            "waiting for."
        ),
        pr.h2("How they are announced"),
        pr.p(
            "The region is an aria-live=polite container, so a toast is read "
            "at the next pause rather than cutting into what is being said. "
            "A danger toast is also mirrored into a separate, always-present "
            'role=alert element, because polite means "when you get a '
            'moment" and a failure cannot wait for one.'
        ),
        pr.p(
            "Nothing moves focus. A toast that stole focus would interrupt "
            "whatever was being typed, and a keyboard user reaches the "
            "dismiss button and any action by tabbing to it like anything "
            "else on the page."
        ),
    )


PAGE = ProsePage(
    slug="toasts",
    title="Toasts",
    nav_label="Toasts",
    group="Guides",
    order=2,
    build=_build,
)
