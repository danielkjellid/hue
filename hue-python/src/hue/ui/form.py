from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.types.core import ComponentType
from hue.ui.atoms.text import Text
from hue.ui.base import AlpineModelMixin, ChainableComponent
from hue.utils import classnames, render_if


class FormControl(AlpineModelMixin, ChainableComponent):
    """
    Shared plumbing for named form controls (the text inputs and the checkbox).

    Owns the name, label, required, disabled, help text and error text
    modifiers, and the ids that tie help and error text to the control through
    aria-describedby and aria-errormessage, so every control wires them up the
    same way.
    """

    def __init__(self, name: str | None = None) -> None:
        super().__init__()
        self._name = name

    def name(self, value: str) -> Self:
        self._name = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def help_text(self, value: str) -> Self:
        self._props["help_text"] = value
        return self

    def error_text(self, value: str) -> Self:
        self._props["error_text"] = value
        return self

    # ------------------------------------------------------------------
    # Helpers for subclasses
    # ------------------------------------------------------------------

    def _require_name(self) -> str:
        if self._name is None:
            raise ValueError(
                f"{type(self).__name__} requires a name; "
                "pass it to the constructor or call .name()."
            )
        return self._name

    def _input_id(self) -> str:
        return self._attrs.get("id") or self._require_name()

    def _help_id(self) -> str | None:
        return f"{self._name}-description" if self._get_prop("help_text") else None

    def _error_id(self) -> str | None:
        return f"{self._name}-error" if self._get_prop("error_text") else None

    def _describedby(self) -> str | None:
        """
        The help and error ids plus anything the caller set via aria_describedby.
        """
        return (
            classnames(
                self._help_id(), self._error_id(), self._attrs.get("aria_describedby")
            )
            or None
        )

    def _control_attrs(self, **own: object) -> dict[str, object]:
        """
        Merge the caller's base attrs (id, ARIA, Alpine) with the control's own,
        where the control's own win and None values are dropped.
        """
        merged = {**self._get_base_html_attrs(), **own}
        return {k: v for k, v in merged.items() if v is not None}

    def _help_text_component(self) -> ComponentType:
        return render_if(
            self._get_prop("help_text"),
            lambda text: Text(text)
            .variant("body")
            .muted()
            .tag(html.span)
            .id(f"{self._name}-description"),
        )

    def _error_text_component(self) -> ComponentType:
        return render_if(
            self._get_prop("error_text"),
            lambda text: Text(text)
            .variant("body")
            .destructive()
            .role("alert")
            .id(f"{self._name}-error"),
        )
