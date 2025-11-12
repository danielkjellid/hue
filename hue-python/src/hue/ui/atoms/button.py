from dataclasses import KW_ONLY, dataclass, field
from typing import Any, Literal

from htmy import Context, html
from typing_extensions import Annotated, Doc

from hue.types.core import BaseComponent, ComponentType
from hue.types.html import AriaHasPopup
from hue.ui.atoms.icon import Icon, IconName
from hue.utils import classnames

type ButtonVariant = Literal[
    "primary",
    "secondary",
    "tertiary",
    "quaternary",
    "outline",
    "transparent",
    "primary-destructive",
    "secondary-destructive",
    "tertiary-destructive",
    "outline-destructive",
    "transparent-destructive",
]
type ButtonSize = Literal["xs-icon", "sm", "md", "lg"]
type ButtonShape = Literal["rounded", "pill"]


@dataclass(slots=True, kw_only=False, frozen=True)
class Button(BaseComponent):
    """
    A class representing an html button element.
    """

    children: ComponentType | tuple[ComponentType, ...] = field(default_factory=tuple)

    _: KW_ONLY
    variant: Annotated[
        ButtonVariant,
        Doc("Determines the variant (color) of the button."),
    ] = "primary"

    size: Annotated[
        ButtonSize,
        Doc("Determines the size of the button."),
    ] = "md"

    shape: Annotated[
        ButtonShape,
        Doc("""
            The shape of the button.
            - `rounded`: Gives rounded corners.
            - `pill`: Gives full border radius, but adapts to the button content.
            """),
    ] = "rounded"

    fluid: Annotated[
        bool,
        Doc("Determines if the button should take up the full width of its container."),
    ] = True

    type: Annotated[
        Literal["button", "submit", "reset"],
        Doc("Determines the type of the button, defaults to `button`."),
    ] = "button"

    disabled: Annotated[
        bool | None, Doc("Determines if the button should be disabled.")
    ] = None

    aria_haspopup: Annotated[
        AriaHasPopup,
        Doc("Determines if the button has a aria-haspopup attribute."),
    ] = None

    def htmy(self, context: Context, **kwargs: Any) -> html.button:
        classes = classnames(
            _get_base_button_classes(
                fluid=self.fluid,
                shape=self.shape,
                variant=self.variant,
                size=self.size,
            ),
            self.class_,
        )

        children = self.ensure_iterable_children(self.children)

        return html.button(
            *children,
            class_=classes,
            tabindex="0",
            type=self.type,
            disabled=self.disabled,
            aria_haspopup=self.aria_haspopup,
            **self.base_props,
        )


@dataclass(slots=True, kw_only=True, frozen=True)
class IconButton(Button):
    name: IconName

    def htmy(self, context: Context, **kwargs: Any) -> html.button:
        icon_classes = classnames(
            {
                "size-5": self.size in {"xs-icon", "sm"},
                "size-6": self.size == "md",
                "size-7": self.size == "lg",
            }
        )
        button_classes = classnames(
            {
                "text-current": self.variant
                in [
                    "primary-destructive",
                    "secondary-destructive",
                    "tertiary-destructive",
                    "outline-destructive",
                    "transparent-destructive",
                ]
            },
            _get_base_button_classes(
                fluid=self.fluid,
                shape=self.shape,
                variant=self.variant,
                size=self.size,
            ),
            self.class_,
        )

        return html.button(
            Icon(name=self.name, class_=icon_classes),
            class_=button_classes,
            tabindex="0",
            type=self.type,
            disabled=self.disabled,
            aria_haspopup=self.aria_haspopup,
            **self.base_props,
        )


def _get_base_button_classes(
    *,
    fluid: bool,
    shape: ButtonShape,
    variant: ButtonVariant,
    size: ButtonSize,
) -> str:
    """
    Get the classes for the base button component.
    """
    variant_classes: dict[ButtonVariant, list[str]] = {
        "primary": [
            "bg-primary",
            "text-white",
            "outline-primary",
            "hover:bg-primary-600",
            "disabled:opacity-50",
        ],
        "secondary": [
            "bg-secondary",
            "text-white",
            "outline-secondary",
            "hover:bg-secondary-700",
            "disabled:bg-secondary-200",
            "dark:text-secondary-900",
            "dark:hover:bg-secondary-800",
            "dark:disabled:text-wg-white-500",
        ],
        "primary-destructive": [
            "bg-destructive",
            "text-white",
            "outline-destructive",
            "hover:bg-destructive-600",
            "disabled:bg-destructive",
        ],
        "secondary-destructive": [
            "bg-destructive",
            "text-white",
            "outline-destructive",
            "hover:bg-destructive-600",
            "disabled:bg-destructive",
            "disabled:opacity-50",
            "dark:text-white",
            "dark:hover:bg-destructive-600",
            "dark:disabled:text-white",
        ],
        "tertiary": [
            "bg-surface",
            "text-surface-900",
            "outline-surface",
            "hover:bg-surface-100",
            "disabled:text-surface-300",
        ],
        "tertiary-destructive": [
            "bg-destructive-50",
            "hover:bg-destructive-100",
            "disabled:bg-destructive-50",
            "dark:bg-surface-100",
            "dark:hover:bg-surface-200",
            "text-destructive-700",
            "outline-destructive",
            "disabled:text-destructive-300",
            "dark:text-destructive-500",
            "dark:disabled:text-destructive/50",
        ],
        "quaternary": [
            "bg-surface-200",
            "text-surface-900",
            "outline-surface",
            "hover:bg-surface-300",
            "disabled:text-surface-300",
        ],
        "outline": [
            "dark:shadow:none",
            "border",
            "border-surface-200",
            "shadow-xs",
            "border",
            "hover:bg-surface",
            "disabled:border-surface-50",
            "dark:border-surface-100",
            "text-surface-900",
            "outline-primary",
            "disabled:text-surface-300",
        ],
        "outline-destructive": [
            "border-destructive",
            "hover:bg-destructive-50",
            "disabled:border-destructive-100",
            "dark:border-destructive",
            "dark:hover:bg-surface",
            "dark:disabled:border-destructive-900",
            "text-destructive-700",
            "outline",
            "outline-destructive",
            "disabled:text-destructive-300",
            "dark:text-destructive-500",
            "dark:disabled:text-destructive/50",
        ],
        "transparent": [
            "bg-transparent",
            "hover:bg-surface",
            "text-surface-900",
            "outline-primary",
            "disabled:text-surface-300",
        ],
        "transparent-destructive": [
            "hover:bg-destructive-50",
            "dark:hover:bg-surface",
            "text-destructive-700",
            "outline-destructive",
            "disabled:text-destructive-300",
            "dark:text-destructive-500",
            "dark:disabled:text-destructive/50",
        ],
    }

    classes = classnames(
        {
            "rounded-lg": shape == "rounded",
            "rounded-full": shape == "pill",
        },
        {
            "w-full": fluid,
            "w-fit": not fluid,
        },
        {
            "gap-0 p-1": size in {"xs-icon", "sm"},
            "gap-1 p-2": size == "md",
            "gap-1 p-3": size == "lg",
        },
        variant_classes[variant],
        "group inline-flex select-none items-center justify-center cursor-pointer",
        "text-sm font-medium leading-6 transition-colors duration-100 antialiased",
        "focus:outline-0 focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-offset-2 disabled:pointer-events-none",
    )

    return classes
