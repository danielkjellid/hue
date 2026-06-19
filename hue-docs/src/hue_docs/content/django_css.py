from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


def _build() -> ComponentType:
    return pr.page(
        pr.h1("CSS and assets"),
        pr.lead(
            "Hue serves its own pre-built CSS and JavaScript straight from the "
            "Python package via a Django middleware — no collectstatic and no "
            "static file configuration for Hue's own component styles."
        ),
        pr.h2("Setup"),
        pr.p("Add the middleware to your MIDDLEWARE setting:"),
        pr.code(
            "# settings.py\n\n"
            "MIDDLEWARE = [\n"
            '    "hue_django.middleware.HueAssetsMiddleware",\n'
            "    # ... your other middleware\n"
            "]"
        ),
        pr.p(
            "That's all. Hue's CSS is now served at /__hue__/styles.css and "
            "its JavaScript at /__hue__/js/alpine.js, directly from the "
            "installed package."
        ),
        pr.h2("Adding your own CSS"),
        pr.p(
            "Build and serve your own styles however you like, then point Hue "
            "at them with HUE_EXTRA_CSS_URLS. Hue adds them as <link> tags "
            "after its own stylesheet, so your rules take precedence over the "
            "defaults."
        ),
        pr.code('# settings.py\n\nHUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]'),
        pr.h2("Overriding colors"),
        pr.p(
            "Hue's theme is driven by CSS variables, so a plain stylesheet "
            "served through Django's staticfiles is enough to retheme it — no "
            "build pipeline required:"
        ),
        pr.code(
            "/* static/my-overrides.css */\n"
            ":root {\n"
            "  --color-primary-500: #8B5CF6;\n"
            "  --color-primary-600: #7C3AED;\n"
            "}",
            language="css",
        ),
        pr.p("Add the file to STATICFILES_DIRS and list it in HUE_EXTRA_CSS_URLS:"),
        pr.code(
            "# settings.py\n\n"
            'STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]\n'
            'HUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]'
        ),
        pr.h2("Using Tailwind for your own code"),
        pr.p(
            "If you want Tailwind utilities in your own markup, run your own "
            "Tailwind build and serve the output through HUE_EXTRA_CSS_URLS. "
            "Hue's CSS covers Hue components; your CSS covers your code."
        ),
        pr.code(
            "/* static/tailwind.input.css */\n"
            '@import "tailwindcss";\n\n'
            "/* Your custom styles — Tailwind compiles utilities from your code */",
            language="css",
        ),
        pr.h2("Accessing Hue's CSS source"),
        pr.p(
            "For deeper customization — for example, importing Hue's theme "
            "tokens into your own Tailwind build — the source stylesheet path "
            "is available from hue.assets:"
        ),
        pr.code(
            "from hue.assets import css_source_path\n\n"
            "print(css_source_path())\n"
            "# /path/to/site-packages/hue/static/styles/tailwind.input.css"
        ),
    )


PAGE = ProsePage(
    slug="django/css",
    title="CSS and assets",
    nav_label="CSS and assets",
    group="Django",
    order=1,
    build=_build,
)
