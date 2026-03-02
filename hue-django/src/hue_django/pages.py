from hue.pages import create_page_base

from hue_django.conf import settings
from hue_django.middleware import HUE_ASSETS_PREFIX

Page = create_page_base(
    css_url=f"{HUE_ASSETS_PREFIX}styles.css",
    js_url=f"{HUE_ASSETS_PREFIX}js/alpine.js",
    html_title_factory=settings.HUE_HTML_TITLE_FACTORY,
    extra_css_urls=settings.HUE_EXTRA_CSS_URLS,
)
