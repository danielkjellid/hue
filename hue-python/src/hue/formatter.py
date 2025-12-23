from typing import Any, Callable

from htmy import Formatter

from hue.types.core import AlpineAjaxProps


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
        # We're dealing with an alpine attribute, so it needs special handling.
        if name.startswith(AlpineAjaxProps.identifier):
            return AlpineAjaxProps.to_html(name)
        else:
            return super()._format_name(name)
