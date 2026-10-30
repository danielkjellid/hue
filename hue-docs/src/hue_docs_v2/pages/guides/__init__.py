"""
Hand-written guides, authored with hue's own components.
"""

from hue_docs_v2.model import GuidePage
from hue_docs_v2.pages.guides import (
    actions,
    contexts,
    django_css,
    django_views,
    fastapi_setup,
    fastapi_views,
    forms,
    framework,
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
    forms.PAGE,
    contexts.PAGE,
    shortcuts.PAGE,
    django_views.PAGE,
    django_css.PAGE,
    fastapi_views.PAGE,
    fastapi_setup.PAGE,
]
