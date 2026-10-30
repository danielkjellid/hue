from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.layout import prose as pr
from hue_docs.model import GuidePage


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
            "Hue's colours are CSS custom properties in two layers. The "
            "`--hue-*` ramps hold the raw palette, and semantic aliases such "
            "as `--color-accent` point at ramp steps. Redefine a ramp step in "
            "a plain stylesheet served through Django's staticfiles, with no "
            "build pipeline, and everything built on it changes in both themes. "
            "The accent reads `--hue-blue-700`, `-800` and `-900` for its fill, "
            "hover and pressed state in light mode, and `-50`, `-100` and `-200` "
            "for its subtle fills and border. Dark mode reads `--hue-blue-300` "
            "to `--hue-blue-500`."
        ),
        pr.code(
            "/* static/my-overrides.css */\n"
            ":root {\n"
            "  --hue-blue-50: #F5F3FF;\n"
            "  --hue-blue-100: #EDE9FE;\n"
            "  --hue-blue-200: #DDD6FE;\n"
            "  --hue-blue-700: #6D28D9;\n"
            "  --hue-blue-800: #5B21B6;\n"
            "  --hue-blue-900: #4C1D95;\n"
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
