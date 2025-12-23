from htmy import html

from hue.spacing import MARGIN, Size


def Spacer(spacing: Size = "sm") -> html.div:
    """
    The spacer component is a component that provides a common interface for
    creating spacing between elements.

    Note: This component will take up space in the DOM as its a div element, which
    can cause layout issues if used in a flex container with defined spacing between.
    """
    _top, _right, bottom, _left = MARGIN[spacing]
    return html.div(class_=bottom)
