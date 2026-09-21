from __future__ import annotations

from htmy import Context
from typing_extensions import Self

from hue.types.core import ComponentType
from hue.ui.base import AlpineModelMixin, ChainableComponent
from hue.ui.molecules.field import Field, error_id, hint_id
from hue.ui.molecules.form import FormErrors
from hue.utils import classnames


class FormControl(AlpineModelMixin, ChainableComponent):
    """
    Shared plumbing for every named form control.

    Owns name, label, required, disabled and error, and the ids that tie the
    supporting text to the control through aria-describedby, so every control
    wires them up the same way.
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

    def _error(self, context: Context) -> str | None:
        """
        What is wrong with this control: what it was told, or failing
        that what the form around it knows about a control of this name.

        Looked up rather than handed down, because a control nested
        inside somebody else's layout is somewhere nothing above it can
        reach.
        """
        own: str | None = self._get_prop("error")
        if own is not None:
            return own
        return FormErrors.from_context(context).of(self._name)

    def _describedby(self, context: Context, *extra: str | None) -> str | None:
        """
        Every id describing this control, plus anything the caller added
        through aria_describedby.

        Errors are described rather than pointed at with aria-errormessage,
        which still has patchy screen-reader support.
        """
        control_id = self._input_id()
        return (
            classnames(
                *extra,
                hint_id(control_id) if self._get_prop("hint") else None,
                error_id(control_id) if self._error(context) else None,
                self._attrs.get("aria_describedby"),
            )
            or None
        )

    def _control_attrs(self, context: Context, **own: object) -> dict[str, object]:
        """
        Merge the caller's base attrs (id, ARIA, Alpine) with the control's own,
        where the control's own win and None values are dropped.
        """
        merged = {**self._get_base_html_attrs(), **own}
        return {k: v for k, v in merged.items() if v is not None}


class FieldControl(FormControl):
    """
    A control with room under it for a note about what to enter.

    The controls that sit in a Field, in other words. A choice - a checkbox, a
    radio, a switch - says its extra line with description() instead, beside
    the control rather than under the whole row, because that is where it
    belongs when the control is one box and a sentence.
    """

    def hint(self, value: str) -> Self:
        """
        A note about what to enter, shown under the control.
        """
        self._props["hint"] = value
        return self

    def _field(self, context: Context, control: ComponentType) -> Field:
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
            .error(self._error(context))
            .content(control)
        )
