from dataclasses import dataclass, fields
from functools import cache, wraps
from typing import Any, Callable

from hue.types.core import BaseComponent, BaseProps, ComponentType


@cache
def _get_base_props_fields() -> set[str]:
    """Lazily compute and cache BaseProps field names."""
    return frozenset(f.name for f in fields(BaseProps))


def class_component(cls: type[BaseComponent]) -> type[BaseComponent]:
    """
    A decorator that converts a class into a class component.
    """
    return dataclass(slots=True, frozen=True, kw_only=False)(cls)


def function_component(
    func: Callable[..., ComponentType],
) -> Callable[..., ComponentType]:
    """
    Decorator for function-based components that automatically extracts BaseProps
    from **kwargs and passes them as `_base_props` dict to the wrapped function.

    Usage:
        @function_component
        def MyComponent(
            *children: ComponentType,
            my_prop: str = "my-prop",
            **base_props: Unpack[BasePropsKwargs],
        ) -> html.div:
            return html.div(*children, class_=..., **_base_props)
    """
    base_props_fields = _get_base_props_fields()

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ComponentType:
        # Separate base props from component-specific kwargs
        base_props: dict[str, Any] = {}
        component_kwargs: dict[str, Any] = {}

        for key, value in kwargs.items():
            if key in base_props_fields and value is not None:
                base_props[key] = value
            else:
                component_kwargs[key] = value

        return func(*args, **base_props, **component_kwargs)

    return wrapper
