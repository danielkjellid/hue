from typing import Any, Callable

from htmy import Formatter


class HueFormatter(Formatter):
    def __init__(
        self,
        *,
        default_formatter: Callable[[Any], str] = str,
        name_formatter: Callable[[str], str] | None = None,
    ) -> None:
        super().__init__(
            default_formatter=default_formatter, name_formatter=name_formatter
        )

    def _format_name(self, name: str) -> str:
        # We're dealing with an alpine atribute, so it needs special handling.
        if name.startswith("x_"):
            return self.format_alpine_attr(name)
        else:
            return super()._format_name(name)

    def format_alpine_attr(self, name: str) -> str:
        """
        Format a Python attribute name to an Alpine.js compatible attribute.
        Examples:
        - 'x_on_click' -> 'x-on:click'
        - 'x_on_click__outside' -> 'x-on:click.outside'
        - 'x_transition__enter_start' -> 'x-transition:enter-start'
        """
        # First split by double underscore to separate modifiers
        base_name, *modifiers = name.split("__")

        if base_name == "x_data":
            return "x-data"
        elif base_name.startswith("x_on_"):
            result = f"x-on:{base_name[5:].replace('_', '-')}"
        elif base_name.startswith("x_transition_"):
            result = f"x-transition:{base_name[13:].replace('_', '-')}"
        elif base_name.startswith("x_bind_"):
            result = f"x-bind:{base_name[7:].replace('_', '-')}"
        elif base_name.startswith("x_"):
            result = f"x-{base_name[2:].replace('_', '-')}"
        else:
            result = f"x-{base_name.replace('_', '-')}"

        # Add any modifiers, converting underscores to hyphens
        if modifiers:
            result += "." + ".".join(mod.replace("_", "-") for mod in modifiers)

        return result
