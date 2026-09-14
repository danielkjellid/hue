# hue-django

Django integration for [hue](../hue-python): class-based views that render hue
pages and Alpine AJAX fragments, a router that understands Django path syntax,
and middleware that serves hue's CSS and JS straight from the package.

## Install

```sh
uv add hue-django
```

```python
# settings.py
MIDDLEWARE = [
    "hue_django.middleware.HueAssetsMiddleware",  # serves /__hue__/styles.css and js
    ...
]
```

## Usage

```python
from django.http import HttpRequest
from hue import html
from hue.context import HueContext
from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView


class LoginView(HueView):
    router = Router[HttpRequest]()

    async def index(self, request: HttpRequest, context: HueContext[HttpRequest]) -> Page:
        return Page(title="Login", body=html.div("Login page"))

    @router.fragment_post("login/")
    async def login(self, request: HttpRequest, context: HueContext[HttpRequest]):
        return html.div("Login successful")


# urls.py
urlpatterns = [path("login/", include(LoginView.urls))]
```

Fragment routes are AJAX-only and return HTML fragments; `index` serves the full
page. Handlers may be sync or async, may return a Django response (a redirect,
say) to pass it through, and may declare a typed `body` parameter to have the
request body parsed and validated with Pydantic. Validation failures return 422
via the overridable `handle_body_validation_error` hook.

`HueFragmentsView` is the same without an `index`, for grouping related
fragments. The Alpine bundle sends the CSRF token as `X-CSRFToken` on AJAX
requests; use `hue_django.ui.CsrfTokenInput` in forms that post without AJAX.

Settings: `HUE_EXTRA_CSS_URLS` (extra stylesheets after hue's) and
`HUE_HTML_TITLE_FACTORY` (callable formatting the document title).
