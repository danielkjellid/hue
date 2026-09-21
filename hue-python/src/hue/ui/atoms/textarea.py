from __future__ import annotations

from typing import override

from htmy import Context, html
from htmy.core import TagConfig
from typing_extensions import Self

from hue.types.core import Component
from hue.ui._styles import FIELD_SHELL
from hue.ui.form import FieldControl
from hue.utils import classnames

# The shell, plus the box a multi-line control needs instead of a fixed height.
_TEXTAREA_CLASSES = classnames(
    FIELD_SHELL,
    "min-h-[84px] px-[11px] py-[9px] text-base leading-[1.55] resize-y",
)


class _Textarea(html.textarea):
    """
    A textarea whose content is not padded onto its own line.

    htmy puts every child on a line of its own, and a textarea keeps each
    character between its tags - so that padding would hand the server back a
    value with a newline on the end of it.
    """

    __slots__ = ()

    # No child separator, which is where the padding comes from.
    tag_config: TagConfig = {}  # noqa: RUF012

    @override
    def _get_htmy_name(self) -> str:
        # The tag name follows the class name, which this one deliberately
        # is not.
        return "textarea"


_AUTOSIZE = "$el.style.height = 'auto'; $el.style.height = $el.scrollHeight + 'px'"


class Textarea(FieldControl):
    """
    A multi-line text input.

    max_length() is a soft limit: it counts what is typed and marks the field
    invalid past the limit rather than refusing the keystroke, because an input
    that silently stops accepting characters reads as a broken keyboard.

        Textarea().name("bio").label("About you").max_length(280)
    """

    category = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .name("description")
            .label("Description")
            .placeholder("What does this workspace do?")
        )

    def placeholder(self, value: str) -> Self:
        self._props["placeholder"] = value
        return self

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def rows(self, value: int) -> Self:
        self._props["rows"] = value
        return self

    def readonly(self, value: bool = True) -> Self:
        self._props["readonly"] = value
        return self

    def max_length(self, value: int) -> Self:
        """
        A limit to show progress against, not one to enforce.

        A counter appears in the label row and turns red past the limit, and
        the control marks itself invalid - but the text is still accepted, so
        the user can see what has to go rather than wondering why typing
        stopped working.
        """
        self._props["max_length"] = value
        return self

    def autosize(self, value: bool = True) -> Self:
        """
        Grow with the text rather than scrolling inside a fixed box.
        """
        self._props["autosize"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def horizontal(self, value: bool = True) -> Self:
        """
        Put the label beside the control rather than above it, for a
        settings page where every row shares one edge.
        """
        self._props["horizontal"] = value
        return self

    def _render(self, context: Context) -> Component:
        name = self._require_name()
        disabled: bool = self._get_prop("disabled", False)
        required: bool = self._get_prop("required", False)
        limit: int | None = self._get_prop("max_length")
        autosize: bool = self._get_prop("autosize", False)
        error: str | None = self._error(context)
        value: str = self._get_prop("value", "")
        control_id = self._input_id()

        # Counting here rather than in a bundled component: it is one number
        # read two ways, and the expressions stay next to the markup they drive.
        steps: list[str] = []
        if limit is not None:
            steps.append("count = $el.value.length")
        if autosize:
            steps.append(_AUTOSIZE)
        on_input = "; ".join(steps)

        textarea_attrs = self._control_attrs(
            context,
            name=name,
            id=control_id,
            class_=classnames(_TEXTAREA_CLASSES, self._get_prop("class_")),
            placeholder=self._get_prop("placeholder"),
            rows=self._get_prop("rows"),
            disabled=disabled or None,
            required=required or None,
            readonly=self._get_prop("readonly", False) or None,
            aria_invalid="true" if error is not None else None,
            aria_describedby=self._describedby(
                context,
            ),
            **(
                {":aria-invalid": f"count > {limit} ? 'true' : null"}
                if limit is not None and error is None
                else {}
            ),
            **({"x-on:input": on_input} if on_input else {}),
            **({"x-init": _AUTOSIZE} if autosize else {}),
        )

        field = self._field(context, _Textarea(value, **textarea_attrs))
        if limit is not None:
            field.x_data({"count": len(value)}).trailing(
                html.span(
                    **{
                        "x-text": f"count + ' / {limit}'",
                        ":class": f"count > {limit} && 'text-danger-text'",
                        "class": "tabular-nums",
                    }
                )
            )
        return field
