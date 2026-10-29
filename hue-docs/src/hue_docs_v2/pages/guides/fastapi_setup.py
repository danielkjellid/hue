from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Setup and CSRF"),
        pr.lead(
            "`configure_hue` attaches Hue to a FastAPI app and serves its CSS "
            "and JavaScript from the installed package. It also turns on "
            "Hue's CSRF protection, or turns it off when you pass "
            "`csrf=None`."
        ),
        pr.h2("configure_hue"),
        pr.p(
            "Call `configure_hue` once, when the app is created. It stores a "
            "`HueConfig` on `app.state` and adds the asset routes. A `Page` "
            "reads the configuration when it renders, so a view on an app "
            "that was never configured raises `HueNotConfiguredError`."
        ),
        pr.code(
            "from fastapi import FastAPI\n"
            "from hue_fastapi import CsrfConfig, configure_hue\n\n"
            "app = FastAPI()\n"
            "configure_hue(app, csrf=CsrfConfig(secret_key=SECRET_KEY))"
        ),
        pr.p(
            "`csrf` is required and has no default, so turning protection "
            "off is always written down. The other arguments are "
            "keyword-only:"
        ),
        pr.bullets(
            [
                "`css_url` replaces Hue's stylesheet with your own, for an "
                "app that compiles Tailwind over its own classes. `None`, the "
                "default, links Hue's.",
                "`js_url` replaces Hue's Alpine bundle with your own build. "
                "`None` links Hue's.",
                "`extra_css_urls` is a sequence of stylesheets linked after "
                "Hue's. The default is empty.",
                "`html_title_factory` formats the document title from a "
                "page's `title`. The default writes `{title} - Hue`.",
                "`formats` is a `Formats` from `hue.formats`, the date and "
                "time formats Hue's components write. The default is "
                "`Formats()`, ISO 8601.",
                "`shortcuts` is the app's `ShortcutRegistry` class, bound on "
                "every page.",
            ]
        ),
        pr.p(
            "The ",
            pr.link("Keyboard shortcuts", "/keyboard-shortcuts/"),
            " guide covers the `ShortcutRegistry`.",
        ),
        pr.code(
            "from hue.formats import Formats\n\n"
            "configure_hue(\n"
            "    app,\n"
            "    csrf=CsrfConfig(secret_key=SECRET_KEY),\n"
            '    extra_css_urls=["/static/overrides.css"],\n'
            '    html_title_factory=lambda title: f"{title} | Acme",\n'
            '    formats=Formats(date="%d.%m.%Y"),\n'
            ")"
        ),
        pr.h2("Hue's assets"),
        pr.p(
            "`configure_hue` serves three files straight from the installed "
            "`hue` package, with no static files step:"
        ),
        pr.bullets(
            [
                "`/__hue__/styles.css`, the stylesheet.",
                "`/__hue__/js/alpine.js`, the Alpine bundle.",
                "`/__hue__/js/chart-bundle.js`, the chart library, which the "
                "Alpine bundle fetches only on a page that shows a chart.",
            ]
        ),
        pr.p(
            "A `Page` links each file with the hash of its content in a `?v=` "
            "query. A request whose `?v=` matches the content is cached for "
            "a year as `immutable`. Any other request gets `no-cache`, and an "
            "`ETag` that answers a matching `If-None-Match` with a 304. When "
            "the app runs with `debug=True`, the files are read again on "
            "every request, so a rebuilt bundle shows up without a restart."
        ),
        pr.h2("CSRF protection"),
        pr.p(
            "Starlette has no CSRF protection of its own, so hue-fastapi "
            "uses a signed double-submit cookie. Hue mints a token, "
            "signs it with `secret_key`, sets it in a cookie and renders the "
            "same value into the page. An unsafe request (any method but "
            "GET, HEAD, OPTIONS and TRACE) must send it back. The server "
            "accepts only a cookie it signed itself, and only when the copy "
            "in the request matches the cookie. A failed check is a 403."
        ),
        pr.p(
            "A request sends its copy in one of two places. Both names are "
            "fixed rather than settings, because Hue depends on them:"
        ),
        pr.bullets(
            [
                "The `X-CSRFToken` header, which the Alpine bundle sends on "
                "every AJAX request.",
                "The `csrf_token` form field, for a form that posts without "
                "AJAX. Put a `CsrfTokenInput` from `hue_fastapi.ui` inside "
                "the form to render it.",
            ]
        ),
        pr.code(
            "from hue import html\n"
            "from hue_fastapi.ui import CsrfTokenInput\n\n"
            "html.form(\n"
            "    CsrfTokenInput(),\n"
            '    html.button("Save").type("submit"),\n'
            ').action("/comments/").method("post")'
        ),
        pr.p(
            "Every unsafe route of a `HueView` or a `HueFragmentsView` is "
            "checked. To protect one of your own endpoints the same way, add "
            "`Depends(csrf_protect)` to it:"
        ),
        pr.code(
            "from fastapi import Depends\n"
            "from hue_fastapi import csrf_protect\n\n"
            '@app.post("/export/", dependencies=[Depends(csrf_protect)])\n'
            "async def export() -> dict[str, str]:\n"
            '    return {"status": "queued"}'
        ),
        pr.h3("CsrfConfig"),
        pr.p("`CsrfConfig` takes `secret_key` and these settings:"),
        pr.bullets(
            [
                '`cookie_name`, `"csrftoken"` by default.',
                "`cookie_secure`, `False` by default. `True` sends the cookie "
                "over HTTPS only and names it with the `__Host-` prefix.",
                '`cookie_samesite`, one of `"lax"`, `"strict"` or `"none"`. '
                'The default is `"lax"`.',
                "`max_age`, how long the cookie lives in seconds. The default "
                "is 52 weeks.",
            ]
        ),
        pr.p(
            "The cookie is `HttpOnly` and its path is `/`. A signed token is "
            "not tied to one browser, so a sibling subdomain could plant a "
            "token it fetched from the site. A browser accepts a `__Host-` "
            "cookie only from the host itself over HTTPS, which closes that "
            "gap. Without `cookie_secure`, serve the app from a domain that no "
            "untrusted subdomain shares."
        ),
        pr.h3("Turning CSRF off"),
        pr.p(
            "Pass `csrf=None` for an app that brings its own protection. Hue "
            "then checks nothing and sets no cookie, the page's token is "
            "empty, and a `CsrfTokenInput` renders an empty value."
        ),
        pr.h2("Toasts across a redirect"),
        pr.p(
            "A toast raised in a handler that returns a redirect has no "
            "markup to ride along with. `HueRequestMiddleware` keeps it in "
            "the session and shows it on the next page. It needs Starlette's "
            "`SessionMiddleware` outside it. Starlette runs the middleware "
            "added last first, so add the session second:"
        ),
        pr.code(
            "from hue_fastapi import HueRequestMiddleware\n"
            "from starlette.middleware.sessions import SessionMiddleware\n\n"
            "app.add_middleware(HueRequestMiddleware)\n"
            "app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)"
        ),
        pr.p(
            "Without the middleware, a hue handler that raises a toast and "
            "returns a redirect raises a `RuntimeError`, so the toast is "
            "never dropped quietly. `HueRequestMiddleware` also lets "
            "`toast()` and `shortcuts.use()` work in a plain FastAPI "
            "endpoint, not only in a hue route."
        ),
        pr.h2("Adding your own CSS"),
        pr.p(
            "Serve your own stylesheet however you like, then list its URL in "
            "`extra_css_urls`. Hue links it after its own stylesheet, so your "
            "rules win over Hue's at equal specificity. FastAPI's "
            "`StaticFiles` is enough:"
        ),
        pr.code(
            "from fastapi.staticfiles import StaticFiles\n\n"
            'app.mount("/static", StaticFiles(directory="static"), name="static")\n'
            "configure_hue(\n"
            "    app,\n"
            "    csrf=CsrfConfig(secret_key=SECRET_KEY),\n"
            '    extra_css_urls=["/static/overrides.css"],\n'
            ")"
        ),
        pr.h2("Overriding colours"),
        pr.p(
            "Hue's colours are CSS custom properties in two layers. The "
            "`--hue-*` ramps hold the raw palette, and semantic aliases such "
            "as `--color-accent` point at ramp steps. Redefine a ramp step in "
            "your stylesheet and everything built on it changes, in both "
            "themes. The accent reads `--hue-blue-700` and `--hue-blue-800` "
            "in light mode, and `--hue-blue-300` to `--hue-blue-500` in dark "
            "mode."
        ),
        pr.code(
            "/* static/overrides.css */\n"
            ":root {\n"
            "  --hue-blue-700: #6D28D9;\n"
            "  --hue-blue-800: #5B21B6;\n"
            "}",
            language="css",
        ),
        pr.h2("Using Tailwind for your own code"),
        pr.p(
            "Hue's built stylesheet holds only the classes Hue itself uses. "
            "To use Tailwind utilities in your own markup, do one of these:"
        ),
        pr.bullets(
            [
                "Build your own stylesheet over your own code and list it in "
                "`extra_css_urls`, beside Hue's.",
                "Build one stylesheet whose Tailwind build sees both Hue's "
                "classes and yours, and pass its URL as `css_url` in place of "
                "Hue's.",
            ]
        ),
        pr.p(
            "Hue's source stylesheet holds its theme tokens. "
            "`css_source_path` in `hue.assets` gives its path:"
        ),
        pr.code(
            "from hue.assets import css_source_path\n\n"
            "print(css_source_path())\n"
            "# /path/to/site-packages/hue/static/styles/tailwind.input.css"
        ),
    )


PAGE = GuidePage(
    slug="fastapi/setup",
    title="Setup and CSRF",
    nav_label="Setup and CSRF",
    group="FastAPI",
    order=1,
    build=_build,
)
