from django.contrib.staticfiles.storage import staticfiles_storage
from hue.pages import create_page_base

from hue_django.conf import settings

Page = create_page_base(
    css_url=staticfiles_storage.url(settings.HUE_CSS_STATIC_PATH),
    js_url=staticfiles_storage.url("hue/js/alpine-bundle.js"),
    html_title_factory=settings.HUE_HTML_TITLE_FACTORY,
)
