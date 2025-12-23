import os
from dataclasses import KW_ONLY, dataclass, field
from typing import Annotated, Any, Literal

from htmy import html
from typing_extensions import Doc

from hue.context import HueContext
from hue.decorators import class_component
from hue.types.core import BaseComponent, ComponentType
from hue.ui.atoms.icon import create_icon_base
from hue.ui.atoms.stack import Stack
from hue.utils import classes_if, classnames, render_if

# Get the path to the icons directory relative to this file
_icons_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "icons")
CalloutIcon = create_icon_base(icons_dir=os.path.abspath(_icons_dir))


@dataclass(slots=True, frozen=True, kw_only=True)
class CiecleInfoIcon(CalloutIcon):  # type: ignore
    name: Literal["circle-info"] = field(default="circle-info", init=False)


type CalloutVariant = Literal[
    "gray",
    "primary",
    "success",
    "info",
    "warning",
    "error",
]


@class_component
class Callout(BaseComponent):
    children: ComponentType | tuple[ComponentType, ...] = field(default_factory=tuple)

    _: KW_ONLY
    title: Annotated[str | None, Doc("The title of the callout.")] = None
    variant: Annotated[
        CalloutVariant,
        Doc("Determines the variant (color) of the callout."),
    ] = "gray"

    def htmy(self, context: HueContext, **kwargs: Any) -> html.div:
        children = self.ensure_iterable_children(self.children)

        return html.div(
            Stack(
                CiecleInfoIcon(
                    class_=classnames(
                        "size-4 flex-shrink-0 items-start mt-1",
                        classes_if(self.variant == "gray", ["text-surface-400"]),
                        classes_if(self.variant == "primary", ["text-primary"]),
                        classes_if(self.variant == "info", ["text-wg-blue"]),
                        classes_if(self.variant == "success", ["text-wg-green"]),
                        classes_if(self.variant == "error", ["text-wg-red"]),
                        classes_if(self.variant == "warning", ["text-wg-yellow"]),
                    )
                ),
                Stack(
                    render_if(
                        self.title,
                        lambda title: html.p(
                            title,
                            class_=classnames(
                                "font-medium leading-6",
                                classes_if(
                                    self.variant in ("gray", "primary"),
                                    ["text-surface-900"],
                                ),
                                classes_if(
                                    self.variant == "info",
                                    ["text-wg-blue-800", "dark:text-wg-blue"],
                                ),
                                classes_if(
                                    self.variant == "success",
                                    ["text-wg-green-800", "dark:text-wg-green"],
                                ),
                                classes_if(
                                    self.variant == "error",
                                    ["text-wg-red-800", "dark:text-wg-red"],
                                ),
                                classes_if(
                                    self.variant == "warning",
                                    ["text-wg-yellow-800", "dark:text-wg-yellow"],
                                ),
                            ),
                        ),
                    ),
                    html.p(*children, class_="max-w-prose"),
                    direction="vertical",
                    spacing="xs",
                ),
                direction="horizontal",
                spacing="sm",
                align_items="items-start",
            ),
            class_=classnames(
                "antialiased flex text-sm leading-6 bg-surface dark:bg-surface",
                "dark:text-surface-500 items-start w-full rounded-lg px-2 py-3 border",
                classes_if(
                    self.variant == "gray",
                    ["border-surface-200", "text-surface-500"],
                ),
                classes_if(
                    self.variant == "primary",
                    ["border-primary", "text-surface-500"],
                ),
                classes_if(
                    self.variant == "success",
                    ["border-wg-green", "bg-wg-green-50", "text-wg-green-700"],
                ),
                classes_if(
                    self.variant == "info",
                    ["border-wg-blue", "bg-wg-blue-50", "text-wg-blue-700"],
                ),
                classes_if(
                    self.variant == "warning",
                    ["border-wg-yellow", "bg-wg-yellow-50", "text-wg-yellow-800"],
                ),
                classes_if(
                    self.variant == "error",
                    ["border-wg-red", "bg-wg-red-50", "text-wg-red-700"],
                ),
            ),
            **self.base_props,
        )
