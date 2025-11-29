from django.contrib.staticfiles.storage import staticfiles_storage

from hue.pages import create_page_base

from hue_django.conf import settings

Page = create_page_base(
    css_url=staticfiles_storage.url(settings.HUE_CSS_STATIC_PATH),
    html_title_factory=settings.HUE_HTML_TITLE_FACTORY,
)
