from importlib.resources import files

from hue.ui import Icon, create_icon_base

from hue_docs.registry import ComponentExample, Showcase, Variant

COMPONENT = Icon

# hue ships its icons inside the installed package; bind an Icon to that set.
_ICONS_DIR = str(files("hue").joinpath("static", "icons"))
_Icon = create_icon_base(icons_dir=_ICONS_DIR)


EXAMPLE = ComponentExample(
    showcases=[
        Showcase(
            title="Sizes & colour",
            layout="row",
            description=(
                "Icons are inlined as SVG, so they take CSS sizing and colour "
                "utilities like any other element."
            ),
            variants=[
                Variant(
                    "size-4",
                    lambda: _Icon("circle-info").class_("size-4 text-surface-900"),
                    'Icon("circle-info").class_("size-4")',
                ),
                Variant(
                    "size-6",
                    lambda: _Icon("circle-info").class_("size-6 text-surface-900"),
                    'Icon("circle-info").class_("size-6")',
                ),
                Variant(
                    "size-8 text-primary",
                    lambda: _Icon("circle-info").class_("size-8 text-primary"),
                    'Icon("circle-info").class_("size-8 text-primary")',
                ),
            ],
        )
    ]
)
