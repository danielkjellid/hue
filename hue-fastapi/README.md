# hue-fastapi

FastAPI integration for [hue](../hue-python). It provides class-based views that render hue pages and Alpine AJAX fragments, a router that reads Starlette's path syntax, signed double-submit CSRF protection, and routes that serve hue's CSS and JS from the installed package.

## Install

```sh
uv add hue-fastapi
```

```python
from fastapi import FastAPI
from hue_fastapi import CsrfConfig, configure_hue

app = FastAPI()
configure_hue(app, csrf=CsrfConfig(secret_key=SECRET_KEY))  # also serves /__hue__/ assets
```

You must pass `csrf`. Setting it to `None` turns hue's CSRF checks off, so the choice is always explicit.

## Usage

```python
from hue import html
from hue.context import HueContext
from hue_fastapi import HueView, Page, Router
from starlette.requests import Request


class LoginView(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(title="Login", body=html.div("Login page"))

    @router.fragment_post("login/")
    async def login(self, request: Request, context: HueContext[Request]):
        return html.div("Login successful")


app.include_router(LoginView.api_router, prefix="/login")
```

`index` serves the full page. Fragment routes are AJAX-only and return HTML fragments. A handler can be sync or async; sync handlers run in a thread pool. A handler can also return a Starlette response, such as a redirect, which is passed through unchanged.

Path parameters use Starlette's syntax (`"items/{item_id:int}/"`). Any parameter after `request` and `context` goes to FastAPI, so you can use path parameters, query parameters and `Depends` as in any other endpoint. To have the body parsed and validated with Pydantic, declare a typed `body` parameter. If validation fails, the view returns 422 through `handle_body_validation_error`, which you can override.

`HueFragmentsView` works like `HueView` without an `index`, for grouping related fragments.

## CSRF

Every unsafe hue route (anything but GET, HEAD, OPTIONS and TRACE) checks the token. The Alpine bundle sends it as `X-CSRFToken` on AJAX requests. A form that posts without AJAX needs `hue_fastapi.ui.CsrfTokenInput` inside it. To protect one of your own endpoints the same way, add `Depends(csrf_protect)` to it (`from hue_fastapi import csrf_protect`).

The token is a signed value in a cookie, checked against the copy the request sends in the `X-CSRFToken` header or the `csrf_token` form field. The signature means the server only accepts tokens it minted. A token is not tied to one browser, so a sibling subdomain could plant one it fetched from the site. With `cookie_secure=True` the cookie is named with the `__Host-` prefix, which browsers accept only from the host itself over HTTPS, and that closes the gap.

`CsrfConfig` takes these settings besides `secret_key`:

| Setting | Default | What it sets |
| --- | --- | --- |
| `cookie_name` | `"csrftoken"` | The cookie's name. |
| `cookie_secure` | `False` | Send the cookie over HTTPS only, under the `__Host-` prefix. Set it to `True` in production. |
| `cookie_samesite` | `"lax"` | The cookie's SameSite attribute. |
| `max_age` | 52 weeks | How long the cookie lives, in seconds. |

## Toasts across a redirect

A toast raised before a redirect is shown on the next page. This needs a session. Add `HueRequestMiddleware`, then Starlette's `SessionMiddleware`; Starlette runs the middleware added last first, so the session wraps hue's middleware:

```python
from starlette.middleware.sessions import SessionMiddleware
from hue_fastapi import HueRequestMiddleware

app.add_middleware(HueRequestMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
```

The same middleware lets `toast()` and `shortcuts.use()` work in plain FastAPI endpoints, not only in hue routes.

## Settings

`configure_hue` also accepts these keyword arguments:

| Argument | Default | What it sets |
| --- | --- | --- |
| `css_url` | hue's own stylesheet | Your stylesheet, if you build Tailwind with your own classes. |
| `js_url` | hue's own bundle | Your script bundle, if you build your own. |
| `extra_css_urls` | `()` | Stylesheets loaded after hue's. |
| `html_title_factory` | `"{title} - Hue"` | A function that formats the document title. |
| `formats` | `Formats()` | Date and time formats. |
| `shortcuts` | `None` | The app's `ShortcutRegistry`, bound on every page. |
