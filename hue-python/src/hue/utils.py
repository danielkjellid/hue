from htmy import ComponentType

from hue.types.core import Undefined


def render_if(
    condition: bool,
    component: ComponentType,
    fallback: ComponentType | Undefined = Undefined,
) -> ComponentType | Undefined:
    """
    Render a component if the condition is true, if not render fallback.
    """
    return component if condition else fallback


def combine_classes(*classes: str | None) -> str:
    """
    Combine CSS class strings, filtering out None values.
    """
    return " ".join(cls for cls in classes if cls is not None)
