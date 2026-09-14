from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.button import Button, ButtonVariant
from hue.ui.base import ChainableComponent
from hue.utils import classnames

# A group draws the buttons' own borders into one shared edge, so a variant
# without a box has nothing to join: ghost is invisible until hovered, and link
# has no control height at all.
_UNSUPPORTED_VARIANTS: frozenset[ButtonVariant] = frozenset({"ghost", "link"})


class ButtonGroup(ChainableComponent):
    """
    Buttons joined into one control, each still doing its own thing.

    Only the geometry is shared: inner corners squared off, outer ones rounded,
    and each button pulled onto its neighbour so the seam is one line rather
    than two. Every button keeps the variant and size it was given, so they
    should all be given the same ones.

    For a choice where exactly one option is on, reach for SegmentedControl.

        ButtonGroup().content(Button()..., Button()...)
    """

    category = "Actions"

    @classmethod
    def example(cls) -> Self:
        return cls().content(
            Button().variant("outline").size("sm").content("Export"),
            Button().variant("outline").size("sm").content("Schedule"),
        )

    def label(self, value: str) -> Self:
        """
        Name the group, for when the buttons only make sense together.
        """
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        label: str | None = self._get_prop("label")

        for child in self._children:
            if isinstance(child, Button):
                variant = child._get_prop("variant", "primary")
                if variant in _UNSUPPORTED_VARIANTS:
                    raise ValueError(
                        f"ButtonGroup cannot join {variant!r} buttons: the group "
                        f"is made of their borders, and that variant has none. "
                        f"Use a variant with a box, or SegmentedControl if you "
                        f"meant a choice."
                    )

        return html.div(
            *self._children,
            class_=classnames(
                "inline-flex [&>*]:relative [&>*]:rounded-none",
                "[&>*:first-child]:rounded-s-md [&>*:last-child]:rounded-e-md",
                # Pulled onto its neighbour so the shared edge is one line, and
                # lifted while focused so the ring is not clipped by the button
                # sitting on top of it.
                "[&>*+*]:-ms-px [&>*:focus-visible]:z-10",
                self._get_prop("class_"),
            ),
            **{
                # An unlabelled group role announces "group" and nothing else.
                **({"role": "group", "aria_label": label} if label else {}),
                **self._get_base_html_attrs(),
            },
        )
