from hue import html
from hue.context import HueContext
from starlette.requests import Request
from starlette.responses import RedirectResponse

from hue_fastapi import CsrfConfig, HueView, Page, Router
from hue_fastapi.ui import CsrfTokenInput
from tests.conftest import AJAX_HEADERS, make_app

CSRF = CsrfConfig(secret_key="test-key")


class FormView(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Form", body=html.form(CsrfTokenInput()))

    @router.fragment_post("save/")
    async def save(self, request: Request, context: HueContext[Request]):
        return html.div("saved")

    @router.fragment_get("go/")
    async def go(self, request: Request, context: HueContext[Request]):
        return RedirectResponse("/after/", status_code=302)


async def test_the_token_in_the_page_matches_the_cookie(client_for):
    """
    The first visit arrives with no cookie. The token rendered into the page has
    to be the one the response is about to set, or the first form post fails.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        response = await client.get("/f/")

    token = response.cookies["csrftoken"]
    assert f'value="{token}"' in response.text


async def test_a_valid_cookie_is_not_set_again(client_for):
    """
    Only a request that minted its token sets the cookie.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        await client.get("/f/")
        again = await client.get("/f/")

    assert "set-cookie" not in again.headers


async def test_a_form_field_is_accepted_without_the_header(client_for):
    """
    Forms that post without AJAX carry the token in a hidden field.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        token = (await client.get("/f/")).cookies["csrftoken"]
        response = await client.post(
            "/f/save/", data={"csrf_token": token}, headers=AJAX_HEADERS
        )

    assert response.status_code == 200


async def test_a_wrong_token_is_refused(client_for):
    """
    A token that is not the one in the cookie is refused, even one the server
    signed itself for someone else.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        await client.get("/f/")
        response = await client.post(
            "/f/save/",
            headers={**AJAX_HEADERS, "X-CSRFToken": CSRF._serializer().dumps("x")},
        )

    assert response.status_code == 403


async def test_an_unsigned_cookie_is_refused(client_for):
    """
    Unsigned double submit would accept any value a client made up. The server
    accepts only tokens it minted.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        client.cookies.set("csrftoken", "planted")
        response = await client.post(
            "/f/save/", headers={**AJAX_HEADERS, "X-CSRFToken": "planted"}
        )

    # The cookie and the header agree, so unsigned double submit would let this
    # through. It is refused because the cookie carries no valid signature.
    assert response.status_code == 403


async def test_a_token_that_is_not_ascii_is_refused_not_an_error(client_for):
    """
    A header the compare cannot take as text is a 403, not a 500.
    """
    async with client_for(make_app(("/f", FormView), csrf=CSRF)) as client:
        await client.get("/f/")
        response = await client.post(
            "/f/save/",
            headers={**AJAX_HEADERS, "X-CSRFToken": "\xe9t\xe9".encode("latin-1")},
        )

    assert response.status_code == 403


async def test_protection_can_be_turned_off(client_for):
    """
    An app bringing its own protection passes csrf=None, and hue stays out of
    the way. The token renders empty rather than breaking the page.
    """
    async with client_for(make_app(("/f", FormView), csrf=None)) as client:
        page = await client.get("/f/")
        response = await client.post("/f/save/", headers=AJAX_HEADERS)

    assert response.status_code == 200
    assert 'value=""' in page.text
    assert "csrftoken" not in page.cookies


async def test_the_cookie_is_set_on_passthrough_responses(client_for):
    """
    A handler returning a framework response still gets the cookie applied.
    Without that, a request whose first stop is a redirect would leave the
    visitor with no token and the next form post would fail.
    """
    app = make_app(("/f", FormView), csrf=CSRF)
    async with client_for(app, follow_redirects=False) as client:
        response = await client.get("/f/go/", headers=AJAX_HEADERS)

    assert response.status_code == 302
    assert response.headers["location"] == "/after/"
    assert response.cookies["csrftoken"]
