from htmy.renderer import Renderer

from hue.context import HueContext, HueContextArgs
from hue.types.core import ComponentType


async def render_tree[T_Request](
    *children: ComponentType,
    context_args: HueContextArgs[T_Request],
) -> str:
    """
    Render a tree of components to a HTML string.
    """
    context = HueContext(*children, **context_args)
    renderer = Renderer()
    result = await renderer.render(context)
    return result
