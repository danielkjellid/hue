from __future__ import annotations

from typing import Literal, NamedTuple

from htmy import html
from typing_extensions import Self

from hue import html as hue_html
from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classes_if_else, classnames

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
        children: list[ComponentType] = [HueIcon(option.icon).class_("size-3.5")]
        if labelled:
            children.append(option.text)

        button = (
            hue_html.button()
            .type("button")
            .class_(
                classnames(
                    "inline-flex items-center justify-center gap-1.5 h-6.5",
                    "rounded-sm text-fg-subtle transition-colors hover:text-fg",
                    "aria-pressed:bg-surface aria-pressed:text-fg",
                    "aria-pressed:shadow-segment cursor-pointer",
                    FOCUS_RING,
                    classes_if_else(
                        labelled,
                        ["w-auto", "px-2.5", "font-ui", "text-sm", "font-semibold"],
                        ["w-7"],
                    ),
                )
            )
            .x_on("click", f"$store.theme.select('{option.choice}')")
            .x_bind("aria-pressed", f"$store.theme.choice === '{option.choice}'")
            .content(*children)
        )

        # The visible text already names the option in the labelled variant;
        # adding aria-label there would override it with different wording.
        return button if labelled else button.aria_label(option.description)

    def _render(self, context: HueContext) -> Component:
        variant: ThemeSwitcherVariant = self._get_prop("variant", "icons")
        labelled = variant == "labelled"

        # A caller-supplied role or label wins, so the group can be renamed or
        # relabelled for a different language.
        attrs = {
            "role": "group",
            "aria_label": "Color theme",
            **self._get_base_html_attrs(),
        }

        return html.div(
            *(self._option(option, labelled) for option in _OPTIONS),
            class_=classnames(
                "inline-flex gap-0.5 p-[3px] rounded-md border border-border",
                "bg-surface-sunken",
                self._get_prop("class_"),
            ),
            **attrs,
        )
