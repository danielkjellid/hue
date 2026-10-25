"""Hand-written prose pages, authored with hue's own components."""

from hue_docs_v2.model import GuidePage
from hue_docs_v2.pages.guides import (
    actions,
    contexts,
    data_tables,
    django_css,
    django_views,
    framework,
    icons,
    installation,
    intro,
    shortcuts,
    usage,
)

# Order here is only a fallback; pages are grouped/sorted by their own metadata.
GUIDES: list[GuidePage] = [
    intro.PAGE,
    installation.PAGE,
    usage.PAGE,
    framework.PAGE,
    actions.PAGE,
    icons.PAGE,
    contexts.PAGE,
    data_tables.PAGE,
    shortcuts.PAGE,
    django_views.PAGE,
    django_css.PAGE,
]
