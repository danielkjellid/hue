from typing import Callable


def concatenate_classes(
    func: Callable[..., list[str]],
) -> Callable[..., str]:
    """
    Decorator that concatenates a list of css classes into a string.
    """

    def wrapper(*args, **kwargs) -> str:
        classes = func(*args, **kwargs)

        if not isinstance(classes, list):
            raise RuntimeError("Decorated function must return a list of classes.")

        return " ".join(classes)

    return wrapper
