"""Hand-written prose pages, authored with hue's own components."""

from hue_docs.content import framework, installation, intro, usage
from hue_docs.models import ProsePage

# Order here is only a fallback; pages are grouped/sorted by their own metadata.
PAGES: list[ProsePage] = [
    intro.PAGE,
    installation.PAGE,
    usage.PAGE,
    framework.PAGE,
]
