from collections.abc import Callable

from hue.types.core import UNDEFINED, ComponentType


def render_if[T: object](
    value: T | None,
    component_factory: Callable[[T], ComponentType],
    fallback: ComponentType = UNDEFINED,
) -> ComponentType:
    """
    Render component_factory(value) when value is not None, otherwise fallback.

    fallback renders to nothing by default, which makes this the idiom for
    optional children: render_if(title, lambda t: html.h2(t)).

    For a flag rather than a value - dismissible, show_value, required - reach
    for render_when instead. This one tests against None, so a False would
    render; writing `flag or None` around it works but says nothing, and the
    lambda then takes an argument it has no use for.
    """
    return component_factory(value) if value is not None else fallback


def render_when(
    condition: bool,
    component: ComponentType,
    fallback: ComponentType = UNDEFINED,
) -> ComponentType:
    """
    Render component when condition is true, otherwise fallback.

    The flag half of render_if, and it takes the component rather than a
    factory: there is no value to hand along, so a callback would only be a
    lambda of no arguments at every call site. The component is built either
    way, which is an element and not a render - the cost of the one that turns
    out not to be used is an object nobody walks.

    Also the way to render an optional collection, whose emptiness is a
    condition rather than a value: render_when(bool(actions), html.div(*actions)).
    """
    return component if condition else fallback


def classnames(*args: str | list[str] | dict[str, bool] | None) -> str:
    """
    Join class names into one space separated string, like the JS classnames
    library.

    Strings and lists are included as-is, dict keys are included when their value
    is truthy, and None and empty strings are dropped.
    """
    classes: list[str] = []

    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, str):
            if arg:
                classes.append(arg)
        elif isinstance(arg, list):
            classes.extend(cls for cls in arg if cls)
        else:
            classes.extend(cls for cls, condition in arg.items() if condition and cls)

    return " ".join(classes)


def classes_if(condition: bool, classes: list[str]) -> dict[str, bool]:
    """
    Gate a whole block of classes on one condition.

    Keeps the classnames dict readable when a single condition would otherwise
    have to be repeated for every class: classes_if(disabled, ["opacity-50",
    "cursor-not-allowed"]).
    """
    return dict.fromkeys(classes, condition)


def classes_if_else(
    condition: bool,
    if_true: list[str],
    if_false: list[str],
) -> dict[str, bool]:
    """
    Pick between two mutually exclusive sets of classes.

    classes_if_else(disabled, ["text-surface-300"], ["text-surface-900"]) marks
    the first set on when the condition holds and the second set on otherwise.
    """
    return {
        **dict.fromkeys(if_true, condition),
        **dict.fromkeys(if_false, not condition),
    }
