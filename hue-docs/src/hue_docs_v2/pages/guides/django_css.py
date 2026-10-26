from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import GuidePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("CSS and assets"),
        pr.lead(
            "Hue serves its own pre-built CSS and JavaScript straight from the "
            "Python package via a Django middleware. Hue's own component styles "
            "need no `collectstatic` and no static file configuration."
        ),
        pr.h2("Setup"),
        pr.p("Add the middleware to your `MIDDLEWARE` setting:"),
        pr.code(
            "# settings.py\n\n"
            "MIDDLEWARE = [\n"
            '    "hue_django.middleware.HueAssetsMiddleware",\n'
            "    # ... your other middleware\n"
            "]"
        ),
        pr.p(
            "That's all. Hue's CSS is now served at `/__hue__/styles.css` and "
            "its JavaScript at `/__hue__/js/alpine.js`, directly from the "
            "installed package. The chart library is served beside it at "
            "`/__hue__/js/chart-bundle.js`, which the JavaScript fetches only on "
            "a page that shows a chart."
        ),
        pr.h2("Adding your own CSS"),
        pr.p(
            "Build and serve your own styles however you like, then point Hue "
            "at them with `HUE_EXTRA_CSS_URLS`. Hue adds them as `<link>` tags "
            "after its own stylesheet, so your rules take precedence over the "
            "defaults."
        ),
        pr.code('# settings.py\n\nHUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]'),
        pr.h2("Overriding colors"),
        pr.p(
            "Hue's theme is driven by CSS variables, so a plain stylesheet "
            "served through Django's staticfiles is enough to retheme it, with "
            "no build pipeline:"
        ),
        pr.code(
            "/* static/my-overrides.css */\n"
            ":root {\n"
            "  --color-primary-500: #8B5CF6;\n"
            "  --color-primary-600: #7C3AED;\n"
            "}",
            language="css",
        ),
        pr.p("Add the file to `STATICFILES_DIRS` and list it in `HUE_EXTRA_CSS_URLS`:"),
        pr.code(
            "# settings.py\n\n"
            'STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]\n'
            'HUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]'
        ),
        pr.h2("Using Tailwind for your own code"),
        pr.p(
            "If you want Tailwind utilities in your own markup, run your own "
            "Tailwind build and serve the output through `HUE_EXTRA_CSS_URLS`. "
            "Hue's CSS covers Hue components; your CSS covers your code."
        ),
        pr.code(
            "/* static/tailwind.input.css */\n"
            '@import "tailwindcss";\n\n'
            "/* Your custom styles: Tailwind compiles utilities from your code */",
            language="css",
        ),
        pr.h2("Accessing Hue's CSS source"),
        pr.p(
            "For deeper customization, such as importing Hue's theme tokens "
            "into your own Tailwind build, the source stylesheet path is "
            "available from `hue.assets`:"
        ),
        pr.code(
            "from hue.assets import css_source_path\n\n"
            "print(css_source_path())\n"
            "# /path/to/site-packages/hue/static/styles/tailwind.input.css"
        ),
    )


PAGE = GuidePage(
    slug="django/css",
    title="CSS and assets",
    nav_label="CSS and assets",
    group="Django",
    order=1,
    build=_build,
)
