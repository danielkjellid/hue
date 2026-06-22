"""Hand-written prose pages, authored with hue's own components."""

from hue_docs.content import (
    django_css,
    django_views,
    framework,
    icons,
    installation,
    intro,
    skeleton_loading,
    usage,
)
from hue_docs.models import ProsePage

# Order here is only a fallback; pages are grouped/sorted by their own metadata.
PAGES: list[ProsePage] = [
    intro.PAGE,
    installation.PAGE,
    usage.PAGE,
    framework.PAGE,
    icons.PAGE,
    skeleton_loading.PAGE,
    django_views.PAGE,
    django_css.PAGE,
]
