from __future__ import annotations

import os

from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.icon import _render_icon
from hue.ui.v2.base import ChainableComponent


class Icon(ChainableComponent):
    """
    A SwiftUI-style chainable icon component.

    Not intended to be used directly — use :func:`create_icon_base` to
    create a base class with ``icons_dir`` pre-configured.

    Example::

        MyIcon = create_icon_base(icons_dir="/path/to/icons")
        MyIcon("calendar").class_("size-4")
    """

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self._name = name

    @property
    def icons_dir(self) -> str:
        raise NotImplementedError("Use create_icon_base() to set icons_dir")

    def _render(self, context: HueContext) -> Component:
        if not self._name:
            return ""

        return _render_icon(
            icon_path=f"{os.path.join(self.icons_dir, self._name)}.svg",
            class_=self._get_prop("class_"),
        )


def create_icon_base(icons_dir: str) -> type[Icon]:
    """
    Factory that returns an Icon subclass with ``icons_dir`` pre-configured.

    Example::

        BaseIcon = create_icon_base(icons_dir="/path/to/icons")

        # Usage — no subclassing needed:
        BaseIcon("calendar").class_("size-4")
        BaseIcon("user").class_("size-6")

    For multiple icon sets::

        OutlineIcon = create_icon_base(icons_dir="/path/to/outline")
        FilledIcon  = create_icon_base(icons_dir="/path/to/filled")
    """

    class _ConfiguredIcon(Icon):
        @property
        def icons_dir(self) -> str:
            return icons_dir

    # Give it a nicer repr
    _ConfiguredIcon.__qualname__ = "Icon"
    _ConfiguredIcon.__name__ = "Icon"

    return _ConfiguredIcon
