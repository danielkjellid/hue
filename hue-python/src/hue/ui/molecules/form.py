from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Mapping

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames


@dataclass(frozen=True, slots=True)
class FormErrors:
    """
    What is wrong with a submission, by the name of the control it is
    wrong about - offered to everything inside the form.

    A control looks itself up rather than being handed its error from
    above, which is the only way one nested inside somebody else's layout
    ever hears about it. Nothing above a control knows where it ended up.
    """

    by_name: Mapping[str, str] = field(default_factory=dict)

    def of(self, name: str | None) -> str | None:
        return None if name is None else self.by_name.get(name)

    @classmethod
    def from_context(cls, context: Context) -> FormErrors:
        found = context.get(cls)
        return found if isinstance(found, cls) else cls()


class Form(ChainableComponent):
    """
    A form, and what came back wrong from the last attempt at it.

    errors() is a mapping of control name to what is wrong with it. Every
    named control inside finds its own, however deeply it is nested and
    whoever laid it out, so a view answers a failed submission by handing
    the whole lot to one place.

        Form().action("/sign-up/").errors(problems).content(...)
    """

    category: ClassVar[str | None] = "Inputs"

    @classmethod
    def example(cls) -> Self:
        return cls().errors({"email": "That address is already registered."})

    def action(self, value: str) -> Self:
        self._props["action"] = value
        return self

    def method(self, value: str) -> Self:
        self._props["method"] = value
        return self

    def errors(self, value: Mapping[str, str]) -> Self:
        """
        What is wrong, by control name. A control given its own error
        keeps it: this is the fallback, not an override.
        """
        self._props["errors"] = dict(value)
        return self

    def htmy_context(self) -> Context:
        return {FormErrors: FormErrors(self._get_prop("errors", {}))}

    def _render(self, context: Context) -> Component:
        return html.form(
            *self._children,
            action=self._get_prop("action"),
            method=self._get_prop("method", "post"),
            class_=classnames("flex flex-col gap-5", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )
