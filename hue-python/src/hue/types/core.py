from htmy import Component as HTMYComponent
from htmy import ComponentType as HTMYComponentType
from htmy import Context


class _Undefined:
    """
    A sentinel component that renders to nothing.

    Use :data:`UNDEFINED` to indicate that a component is not supposed to be
    rendered.
    """

    def htmy(self, context: Context, /) -> "Component":
        return ""


UNDEFINED = _Undefined()

type Component = HTMYComponent
type ComponentType = HTMYComponentType
