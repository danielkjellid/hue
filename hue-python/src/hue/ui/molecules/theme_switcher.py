from __future__ import annotations

from typing import Literal, NamedTuple

from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules.segmented_control import SegmentedControl, SegmentedOption
from hue.utils import classnames

type ThemeSwitcherVariant = Literal["icons", "labelled"]


class _Option(NamedTuple):
    choice: str
    icon: str
    #: Shown in the labelled variant.
    text: str
    #: Announced in the icons variant. Names the theme the button selects, not
    #: the icon it shows.
    description: str


_OPTIONS = (
    _Option("light", "sun", "Light", "Light theme"),
    _Option("dark", "moon", "Dark", "Dark theme"),
    _Option("system", "monitor", "System", "Match system"),
)


class ThemeSwitcher(ChainableComponent):
    """
    Lets the visitor pick the colour theme: light, dark or system.

    The choice is remembered under the page's theme_storage_key. Only the
    resolved light or dark reaches data-theme on <html>, so "system" keeps
    following the OS for as long as it stays selected.
    """

    category = "Utility"

    @classmethod
    def example(cls) -> Self:
        return cls().variant("labelled")

    def variant(self, value: ThemeSwitcherVariant) -> Self:
        self._props["variant"] = value
        return self

    def _option(self, option: _Option, labelled: bool) -> ComponentType:
        # No value() on the control, so the pressed state is left to these
        # bindings: which theme is on is only known in the browser.
        segment = (
            SegmentedOption()
            .value(option.choice)
            .x_on("click", f"$store.theme.select('{option.choice}')")
            .x_bind("aria-pressed", f"$store.theme.choice === '{option.choice}'")
        )

        icon = HueIcon(option.icon)
        if labelled:
            # The visible text names the option, so a label here would only
            # override it with different wording.
            return segment.content(icon, option.text)
        return segment.icon_only(option.description).content(icon)

    def _render(self, context: HueContext) -> Component:
        variant: ThemeSwitcherVariant = self._get_prop("variant", "icons")
        labelled = variant == "labelled"

        control = (
            SegmentedControl()
            .size("sm")
            .label("Color theme")
            .class_(classnames(self._get_prop("class_")))
            .content(*(self._option(option, labelled) for option in _OPTIONS))
        )

        # This renders as the control, so the caller's own attributes belong on
        # it - including an aria-label, which then wins over the default above.
        control._attrs.update(self._get_base_html_attrs())
        return control
