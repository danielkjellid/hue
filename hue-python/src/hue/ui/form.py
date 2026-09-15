from __future__ import annotations

from typing_extensions import Self

from hue.types.core import ComponentType
from hue.ui.base import AlpineModelMixin, ChainableComponent
from hue.ui.molecules.field import Field, error_id, hint_id
from hue.utils import classnames


class FormControl(AlpineModelMixin, ChainableComponent):
    """
    Shared plumbing for named form controls (the text inputs and the checkbox).

    Owns name, label, required, disabled, hint and error, and the ids
    that tie the hint and the error to the control through aria-describedby, so
    every control wires them up the same way.
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

    def hint(self, value: str) -> Self:
        """
        A note about what to enter, shown under the control.
        """
        self._props["hint"] = value
        return self

    def error(self, value: str) -> Self:
        """
        What is wrong with the value. Marks the control invalid and replaces
        the hint.
        """
        self._props["error"] = value
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

    def _describedby(self) -> str | None:
        """
        The hint and error ids plus anything the caller set via aria_describedby.

        Errors are described rather than pointed at with aria-errormessage,
        which still has patchy screen-reader support.
        """
        control_id = self._input_id()
        return (
            classnames(
                hint_id(control_id) if self._get_prop("hint") else None,
                error_id(control_id) if self._get_prop("error") else None,
                self._attrs.get("aria_describedby"),
            )
            or None
        )

    def _field(self, control: ComponentType) -> Field:
        """
        The Field every named control renders into, filled from its own props.

        Here rather than in each control because they all answer the same
        questions the same way, and a control that grew its own answer would
        be the one that looked different for no reason.
        """
        return (
            Field()
            .label(self._get_prop("label") or self._require_name())
            .html_for(self._input_id())
            .layout(self._get_prop("layout", "stacked"))
            .required(self._get_prop("required", False))
            .disabled(self._get_prop("disabled", False))
            .hidden_label(self._get_prop("hidden_label", False))
            .hint(self._get_prop("hint"))
            .error(self._get_prop("error"))
            .content(control)
        )

    def _control_attrs(self, **own: object) -> dict[str, object]:
        """
        Merge the caller's base attrs (id, ARIA, Alpine) with the control's own,
        where the control's own win and None values are dropped.
        """
        merged = {**self._get_base_html_attrs(), **own}
        return {k: v for k, v in merged.items() if v is not None}
