from dataclasses import dataclass, fields
from functools import cache, wraps
from typing import Any, Callable, overload

from hue.types.core import BaseComponent, BaseProps


@cache
def _get_base_props_fields() -> frozenset[str]:
    """Lazily compute and cache BaseProps field names."""
    return frozenset(f.name for f in fields(BaseProps))


@overload
def class_component[T: BaseComponent](cls: type[T]) -> type[T]: ...


@overload
def class_component[T: BaseComponent](
    cls: None = None, *, kw_only: bool = False
) -> Callable[[type[T]], type[T]]: ...


def class_component[T: BaseComponent](
    cls: type[T] | None = None, *, kw_only: bool = False
) -> type[T] | Callable[[type[T]], type[T]]:
    """
    A decorator that converts a class into a class component.

    Can be used as:
        @class_component
        class MyComponent(BaseComponent): ...

    Or with arguments:
        @class_component(kw_only=True)
        class MyComponent(BaseComponent): ...
    """

    def decorator(cls: type[T]) -> type[T]:
        return dataclass(slots=True, frozen=True, kw_only=kw_only)(cls)

    if cls is not None:
        # Called as @class_component without parentheses
        return decorator(cls)

    # Called as @class_component(kw_only=True)
    return decorator


def function_component[F: Callable[..., Any]](func: F) -> F:
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
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Separate base props from component-specific kwargs
        base_props: dict[str, Any] = {}
        component_kwargs: dict[str, Any] = {}

        for key, value in kwargs.items():
            if key in base_props_fields and value is not None:
                base_props[key] = value
            else:
                component_kwargs[key] = value

        return func(*args, **base_props, **component_kwargs)

    return wrapper  # type: ignore[return-value]
