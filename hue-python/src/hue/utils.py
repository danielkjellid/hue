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
