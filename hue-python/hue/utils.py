from hue.types.core import ComponentType, Undefined


def render_if(
    condition: bool,
    component: ComponentType,
    fallback: ComponentType | Undefined = Undefined,
) -> ComponentType | Undefined:
    """
    Render a component if the condition is true, if not render fallback.
    """
    return component if condition else fallback


def classnames(*args: str | list[str] | dict[str, bool] | None) -> str:
    """
    A utility for constructing className strings conditionally.
    Similar to the JavaScript classnames library.

    Args:
        *args: Variable number of arguments that can be:
            - str: A class name string
            - list[str]: A list of class names
            - dict[str, bool]: A dictionary where keys are class names and values
              determine if the class should be included
            - None: Ignored

    Returns:
        A space-separated string of class names.

    Examples:
        >>> classnames("foo", "bar")
        'foo bar'
        >>> classnames(["foo", "bar"], "baz")
        'foo bar baz'
        >>> classnames("foo", {"bar": True, "baz": False})
        'foo bar'
        >>> classnames("foo", None, ["bar", "baz"])
        'foo bar baz'
    """
    classes: list[str] = []

    for arg in args:
        if arg is None:
            continue
        elif isinstance(arg, str):
            if arg:  # Only add non-empty strings
                classes.append(arg)
        elif isinstance(arg, list):
            classes.extend([cls for cls in arg if cls])
        elif isinstance(arg, dict):
            classes.extend([cls for cls, condition in arg.items() if condition and cls])
        else:
            # Handle other types by converting to string (for flexibility)
            str_arg = str(arg)
            if str_arg:
                classes.append(str_arg)

    return " ".join(classes)


def classes_if(
    condition: bool,
    classes: list[str],
) -> dict[str, bool]:
    """
    A utility for constructing a dictionary of classes and their conditions. This is
    useful in the event where the keyname consists of so many classes that it would
    be so long that it would be difficult to read.

    Args:
        classes: A list of class names to conditionally include.
        condition: If True, all classes will be included; if False, none will be.

    Returns:
        A dictionary mapping each class to the condition value.

    Examples:
        >>> classes_if(["foo", "bar"], True)
        {'foo': True, 'bar': True}
        >>> classes_if(["foo", "bar"], False)
        {'foo': False, 'bar': False}
    """
    return dict.fromkeys(classes, condition)


def classes_if_else(
    condition: bool,
    if_true: list[str],
    if_false: list[str],
) -> dict[str, bool]:
    """
    A ternary utility for constructing a dictionary of classes based on a condition.
    Returns classes from the first list if condition is True, otherwise from the
    second list.

    This is useful when you have mutually exclusive sets of classes based on a
    condition, avoiding the need to use `not condition` in separate calls.

    Args:
        classes_if_true: Classes to include when condition is True.
        condition: The condition to evaluate.
        classes_if_false: Classes to include when condition is False.

    Returns:
        A dictionary mapping classes to their condition values.

    Examples:
        >>> classes_if_else(["enabled"], True, ["disabled"])
        {'enabled': True, 'disabled': False}
        >>> classes_if_else(["enabled"], False, ["disabled"])
        {'enabled': False, 'disabled': True}
    """
    result: dict[str, bool] = {}
    result.update(dict.fromkeys(if_true, condition))
    result.update(dict.fromkeys(if_false, not condition))
    return result
