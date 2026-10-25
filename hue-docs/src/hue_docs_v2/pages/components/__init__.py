"""
One module per component, each declaring PAGE.
"""

from hue_docs_v2.model import ComponentPage
from hue_docs_v2.pages.components import button, text_input, toast

COMPONENTS: list[ComponentPage] = [button.PAGE, text_input.PAGE, toast.PAGE]
