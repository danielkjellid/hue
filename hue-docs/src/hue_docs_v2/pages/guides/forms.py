from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage

_FIELDS = """from dataclasses import dataclass
from typing import Literal

from hue.ui import Button, Checkbox, Form, NativeSelect, TextInput


@dataclass
class Invite:
    email: str
    role: Literal["member", "admin"] = "member"
    notify: bool = False


def invite_fields(invite: Invite) -> tuple[ComponentType, ...]:
    return (
        TextInput().name("email").label("Email").value(invite.email),
        NativeSelect()
        .name("role")
        .label("Role")
        .options([("member", "Member"), ("admin", "Admin")])
        .value(invite.role),
        Checkbox()
        .name("notify")
        .label("Email me when they join")
        .checked(invite.notify),
        Button().type("submit").variant("primary").content("Send invite"),
    )


def invite_form(invite: Invite, errors: dict[str, str] | None = None) -> Form:
    return Form().id("invite").errors(errors or {}).content(*invite_fields(invite))"""

_PAGE_FORM = """from hue import html

html.form(*invite_fields(Invite(email=""))).id("invite").action(
    "/team/invite/"
).method("POST").x_target("invite").class_("flex flex-col gap-5")"""

_ROUTE = """from hue import toast
from hue.router import HueResponse
from hue_fastapi import HueFragmentsView, Router  # or from hue_django


class Team(HueFragmentsView):
    router = Router[Request]()  # Router[HttpRequest]() with hue-django

    @router.fragment_post("invite/")
    async def invite(self, request, context, body: Invite):
        if await is_member(body.email):
            return HueResponse(
                invite_form(body, errors={"email": "Already on the team."}),
                status_code=422,
            )
        await send_invite(body)
        toast.success(f"Invitation sent to {body.email}")
        return invite_form(Invite(email=""))"""

_HOOK = """from starlette.responses import HTMLResponse


class Team(HueFragmentsView):
    router = Router[Request]()

    async def handle_body_validation_error(self, request, exc):
        errors = {str(e["loc"][0]): e["msg"] for e in exc.errors if e.get("loc")}
        posted = await request.form()
        typed = Invite(email=str(posted.get("email", "")), notify="notify" in posted)
        html = await self.router.render(invite_form(typed, errors), request)
        return HTMLResponse(html, status_code=422)"""

_REDIRECT = """# hue-django
from django.shortcuts import redirect

return redirect(f"/team/{member.id}/")

# hue-fastapi
from starlette.responses import RedirectResponse

return RedirectResponse(f"/team/{member.id}/", status_code=303)"""

_PLAIN = """# hue-django
from hue_django.ui import CsrfTokenInput

# hue-fastapi
from hue_fastapi.ui import CsrfTokenInput

Form().action("/team/invite/").content(
    CsrfTokenInput(),
    *invite_fields(Invite(email="")),
)"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Forms"),
        pr.lead(
            "A form in Hue is built from named controls, posted to one of "
            "your routes with Alpine AJAX, and validated against a type you "
            "declare on the route. The response replaces the form, with "
            "errors on the controls they belong to or with whatever comes "
            "after a successful submission."
        ),
        pr.h2("Controls and names"),
        pr.p(
            "Every control that submits a value subclasses `FormControl`: "
            "`TextInput`, `EmailInput`, `NumberInput`, `PasswordInput`, "
            "`Textarea`, `NativeSelect`, `Select`, `Checkbox` and the other "
            "named controls. "
            "Each takes its name from `name()`, which sets the submitted "
            "name, the control's `id`, the label's `for`, and the ids its "
            "hint and error hang off. A control without `label()` shows its "
            "name as the label. Give each control on a page a name of its own, "
            "or set `id()`, because two controls with one name get one id."
        ),
        pr.p(
            "The examples on this page share one body type, `Invite`, and one "
            "function that builds the controls from it. The route validates "
            "against `Invite`, and the same function draws the form again "
            "with what was typed."
        ),
        pr.code(_FIELDS),
        pr.bullets(
            [
                "`value()` fills a `TextInput`, a `Textarea`, a `NativeSelect` "
                "or a `Select`. `checked()` ticks a `Checkbox`.",
                '`Button` renders `type="button"` unless told otherwise, so '
                'the button that sends the form needs `type("submit")`.',
                "`Select` submits its value through a hidden input under its "
                "name, so a route reads it the same way as a `NativeSelect`.",
            ]
        ),
        pr.p(
            "See ",
            pr.link("TextInput", "/components/text-input/"),
            " for the anatomy every field control shares: label, hint, error, "
            "prefix and suffix.",
        ),
        pr.h2("Posting a form to a route"),
        pr.p(
            "Alpine AJAX takes over a form that carries `x-target`, posts it "
            "with `fetch`, and merges the response into the element whose id "
            "`x-target` names. Hue's own `html.form` has `x_target()`. The "
            "`Form` component does not have one yet, so a `Form` on the page "
            "posts as an ordinary browser form, which a fragment route turns "
            "away (see the section on forms without JavaScript below). Draw "
            "the form on the page with `html.form`, give it an id, and point "
            "`x_target()` at that id."
        ),
        pr.code(_PAGE_FORM),
        pr.p(
            "Hue sets Alpine AJAX's merge strategy to `update`. The element "
            "on the page keeps its own attributes, `x-target` included, and "
            "takes the children of the element with the same id in the "
            "response. That is what lets the route answer with a `Form`, "
            "whose `errors()` the controls read, while the form on the page "
            "stays an `html.form`. Give the page's `html.form` the classes "
            "`Form` would have added, `flex flex-col gap-5`, so the layout "
            "matches."
        ),
        pr.p(
            "The route is a `fragment_post`. A parameter named `body`, typed "
            "as a dataclass or a pydantic model, receives the submitted "
            "fields after Hue has validated them. The URL in `action()` is "
            "wherever the view is mounted plus the route's path."
        ),
        pr.code(_ROUTE),
        pr.p(
            "The router reads `body` from the type annotation when the route "
            "is registered. A `body` parameter without an annotation raises a "
            "`TypeError` at that point, not on the first request."
        ),
        pr.h2("How form fields map to the body"),
        pr.p(
            "A form posts names and strings. Hue turns them into a mapping "
            "and pydantic validates the mapping against the body type. A "
            "request sent as `application/json` is decoded and validated as "
            "it is. Anything else is read as form fields, with these rules."
        ),
        pr.bullets(
            [
                "A field the form does not send takes its default. A field "
                "with no default fails validation as missing.",
                "A text control sends its text even when it is empty, so an "
                'empty `TextInput` arrives as `""`. A `str | None` field '
                'receives `""`, not `None`, and an `int` field rejects it.',
                "An unticked `Checkbox` sends nothing, so its field takes its "
                "default. A ticked one sends its `value()`, or `on` without "
                "one, which a `bool` field reads as `True`.",
                "A name sent more than once, by checkboxes that share it or a "
                "`Combobox` with several choices, fills a field declared as a "
                "`list`, a `tuple` or a `set` with every value. Any other "
                "field receives the last value sent under that name.",
                "Fields the type does not declare, such as a CSRF field, are ignored.",
                "File uploads do not reach the body. Hue reads text fields only.",
            ]
        ),
        pr.h2("Showing errors on controls"),
        pr.p(
            "`Form().errors()` takes a mapping of control name to message. "
            "It offers the mapping to everything inside it through the "
            "`FormErrors` context, and every named control looks up its own "
            "entry, however deep in somebody else's layout it sits. ",
            pr.link("Contexts", "/contexts/"),
            " explains the mechanism.",
        ),
        pr.p(
            "A control with an error sets `aria-invalid`, shows the message in "
            'place of its hint with `role="alert"`, and adds the message\'s '
            "id to its `aria-describedby`. A message set on the control with "
            "`error()` wins over the one from `Form`."
        ),
        pr.p(
            "To keep what the user typed, build the controls again from the "
            "body, as `invite_form(body, errors=...)` does in the route above. "
            "Wrap the result in `HueResponse(..., status_code=422)` to send it "
            "with a 422. Alpine AJAX merges an error response into the target "
            "the same way it merges a successful one."
        ),
        pr.h2("When the body fails validation"),
        pr.p(
            "When the fields do not fit the body type, the handler never runs. "
            "The view's `handle_body_validation_error(request, exc)` answers "
            "instead. Its default response is a 422 with plain text: "
            "`Request body validation failed` followed by the errors. "
            "`exc.errors` holds pydantic's error details, each with a `loc` "
            "naming the field and a `msg`."
        ),
        pr.p(
            "In `hue-fastapi` the hook is a coroutine, so an override can draw "
            "the form again with `self.router.render(component, request)`. "
            "The posted fields are on `await request.form()`, because "
            "`hue-fastapi` has already read the body."
        ),
        pr.code(_HOOK),
        pr.p(
            "In `hue-django` the hook is a plain method, and Hue's renderer is "
            "async, so the hook cannot await it to draw a component. It can "
            "return any `HttpResponse`. To show an error on a control with "
            "`hue-django`, declare only what the form always sends in the body "
            "type and make the check in the handler, which can return a "
            "`HueResponse` as above."
        ),
        pr.h2("Answering a successful submission"),
        pr.p("A route that accepted the form has three ways to answer."),
        pr.bullets(
            [
                "Return a component. Its outermost element needs the id the "
                "form targets, or wrap it in `HueResponse(target=...)`, which "
                "adds a `div` with that id. The route above returns an empty "
                "`invite_form`.",
                "Raise a toast with `toast.success()`, or another method of "
                "`toast` from `hue`. The toast rides along behind the fragment. A "
                "form with `x-target` also updates the page's synced elements, "
                "and the toast region is one of them.",
                "Return your framework's redirect. Hue passes any result with "
                "a `status_code` through untouched.",
            ]
        ),
        pr.code(_REDIRECT),
        pr.p(
            "Starlette's `RedirectResponse` defaults to 307, which makes the "
            "browser send the POST again to the new URL. Pass "
            "`status_code=303` to have it follow with a GET."
        ),
        pr.p(
            "`fetch` follows the redirect, and Alpine AJAX merges the target "
            "from the page it lands on. When that page has no element with the "
            "target's id, Alpine AJAX removes the target from the page. Call "
            '`x_target_away("_top")` on the `html.form` to load the new page '
            "whole instead."
        ),
        pr.p(
            "A toast raised before a redirect has no markup to ride on. "
            "Without `HueRequestMiddleware` the router raises a "
            "`RuntimeError`. With it, the toast waits in the session and "
            "arrives with the page after the redirect. `hue-django` needs "
            "Django's `SessionMiddleware` ahead of "
            "`hue_django.middleware.HueRequestMiddleware`. `hue-fastapi` "
            "needs Starlette's `SessionMiddleware` outside "
            "`hue_fastapi.HueRequestMiddleware`."
        ),
        pr.h2("CSRF tokens in forms"),
        pr.p(
            "A form that posts through Alpine AJAX needs nothing from you. "
            "Hue's Alpine bundle sends the token as the `X-CSRFToken` header "
            "on every request Alpine AJAX makes, using the token the page was "
            "rendered with."
        ),
        pr.h3("hue-django"),
        pr.p(
            "The token is Django's own, and Django's `CsrfViewMiddleware` "
            "checks it. `X-CSRFToken` is the header Django reads by default. "
            "A form that posts without AJAX carries the token in "
            "`csrfmiddlewaretoken`, which `hue_django.ui.CsrfTokenInput` "
            "renders."
        ),
        pr.h3("hue-fastapi"),
        pr.p(
            "Starlette has no CSRF protection, so `hue-fastapi` brings a signed "
            "double-submit cookie, set up with "
            "`configure_hue(app, csrf=CsrfConfig(secret_key=...))`. Every hue "
            "route with an unsafe method checks the cookie against the "
            "`X-CSRFToken` header, or the `csrf_token` form field when there "
            "is no header, and answers 403 when they do not match. "
            "`hue_fastapi.ui.CsrfTokenInput` renders the field. See ",
            pr.link("Setup and CSRF", "/fastapi/setup/"),
            " for the cookie's settings.",
        ),
        pr.h2("Forms without JavaScript"),
        pr.p(
            "Hue's fragment routes only answer Alpine AJAX. A request without "
            "its `X-Alpine-Request` header, or `X-Requested-With: "
            "XMLHttpRequest`, gets a 400 with `AJAX request required`. A "
            "view's page route only answers GET. A form that has to work "
            "before or without JavaScript therefore cannot post to a hue "
            "route, and a form with `x-target` falls back to the same 400 "
            "when Alpine has not loaded."
        ),
        pr.p(
            "A `Form` with no `x-target` posts as a plain browser form to "
            "whatever `action()` names, by POST unless `method()` says "
            "otherwise. Point it at a view of your own framework's, put a "
            "`CsrfTokenInput` inside, and answer with a page."
        ),
        pr.code(_PLAIN),
        Alert()
        .variant("info")
        .title("A plain endpoint in hue-fastapi")
        .content(
            pr.rich(
                "`hue-fastapi` checks CSRF only on hue's own routes. Add "
                "`Depends(csrf_protect)`, from `hue_fastapi`, to an endpoint "
                "of your own that takes a form."
            )
        ),
    )


PAGE = GuidePage(
    slug="forms",
    title="Forms",
    nav_label="Forms",
    group="Guides",
    order=2,
    build=_build,
)
