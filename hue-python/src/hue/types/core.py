from htmy import Component as HTMYComponent
from htmy import ComponentType as HTMYComponentType
from htmy import Context


class _Undefined:
    """
    A sentinel component that renders to nothing.

    Use UNDEFINED where a component slot should stay empty.
    """

    def htmy(self, context: Context, /) -> "Component":
        return ""


UNDEFINED = _Undefined()

type Component = HTMYComponent
type ComponentType = HTMYComponentType
