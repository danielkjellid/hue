"""An interactive component playground driven entirely by the bundled Alpine.

Because the site is static, we pre-render every combination of the component's
enum/bool props server-side and let Alpine ``x-show`` reveal the one matching
the current control selection. A props table below the preview drives that
selection (``x-model``). Everything is derived from the discovered component —
the preview base is its ``example()`` instance.
"""

from __future__ import annotations

import itertools
from typing import Any

from htmy import SafeStr
from hue import html
from hue.types.core import ComponentType

from hue_docs.discovery import Axis, ComponentDoc
from hue_docs.layout.code import code_block
from hue_docs.registry import _format_call, example_instance, playground_axes
from hue_docs.render import render_html_sync

# Upper bound on pre-rendered combinations per component — every combination is
# emitted as hidden HTML, so this caps page weight. Lowest-priority props (see
# playground_axes) are dropped first when the product exceeds this.
_MAX_COMBINATIONS = 64


def _axis_values(axis: Axis) -> tuple[Any, ...]:
    return tuple(axis.values) if axis.kind == "enum" else (False, True)


def _resolve_controls(doc: ComponentDoc) -> list[Axis]:
    controls = playground_axes(doc)

    def combinations(axes: list[Axis]) -> int:
        total = 1
        for axis in axes:
            total *= len(_axis_values(axis))
        return total

    dropped: list[str] = []
    while len(controls) > 1 and combinations(controls) > _MAX_COMBINATIONS:
        dropped.append(controls.pop().method)
    if dropped:
        print(
            f"  playground[{doc.name}]: capped at {_MAX_COMBINATIONS} combos, "
            f"dropped {', '.join(dropped)}"
        )
    return controls


def _js_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return f"'{value}'"


def _default(axis: Axis) -> Any:
    if axis.kind == "bool":
        return False
    if axis.default in axis.values:
        return axis.default
    return axis.values[0]


def _preview(component: ComponentType) -> ComponentType:
    try:
        return SafeStr(render_html_sync(component))
    except Exception as exc:  # defensive, mirrors the static showcase
        return html.p(f"Could not render: {exc}").class_("text-sm text-destructive")


def _combination_block(
    doc: ComponentDoc,
    controls: list[Axis],
    combo: tuple[Any, ...],
) -> ComponentType:
    condition = " && ".join(
        f"sel.{axis.method} === {_js_literal(value)}"
        for axis, value in zip(controls, combo, strict=True)
    )

    instance = example_instance(doc)
    for axis, value in zip(controls, combo, strict=True):
        getattr(instance, axis.method)(value)

    calls = "".join(
        _format_call(axis.method, value)
        for axis, value in zip(controls, combo, strict=True)
    )
    code = f"{doc.name}(){calls}"

    return (
        html.div(
            html.div(_preview(instance)).class_(
                "flex min-h-28 flex-wrap items-center justify-center gap-3 "
                "rounded-lg border border-surface-200 bg-background px-6 py-8"
            ),
            code_block(code),
        )
        .class_("space-y-2")
        .attr("x-show", condition)
        .x_cloak()
    )


def _control_widget(axis: Axis) -> ComponentType:
    model = f"sel.{axis.method}"
    if axis.kind == "bool":
        return (
            html.input_()
            .attr("type", "checkbox")
            .x_model(model)
            .class_("h-4 w-4 rounded border-surface-300 accent-primary")
        )
    return (
        html.select(*[html.option(value).attr("value", value) for value in axis.values])
        .x_model(model)
        .class_(
            "rounded-md border border-surface-200 bg-background px-2 py-1 "
            "text-sm text-surface-900"
        )
    )


def _controls_table(controls: list[Axis]) -> ComponentType:
    rows = [
        html.tr(
            html.td(html.code(axis.method.replace("_", " "))).class_(
                "border-t border-surface-200 px-3 py-2 align-middle text-surface-900"
            ),
            html.td(_control_widget(axis)).class_(
                "border-t border-surface-200 px-3 py-2 align-middle"
            ),
        )
        for axis in controls
    ]
    header = html.tr(
        html.th("Prop").class_("px-3 py-2 text-left font-medium text-surface-500"),
        html.th("Value").class_("px-3 py-2 text-left font-medium text-surface-500"),
    )
    return html.table(
        html.thead(header),
        html.tbody(*rows),
    ).class_("w-full overflow-hidden rounded-lg border border-surface-200 text-sm")


def playground(doc: ComponentDoc) -> ComponentType | None:
    controls = _resolve_controls(doc)
    if not controls:
        return None

    # Probe the example base: skip the playground if it can't render (e.g. a
    # component that requires constructor args and defines no example()).
    try:
        render_html_sync(example_instance(doc))
    except Exception:
        return None

    init = ", ".join(
        f"{axis.method}: {_js_literal(_default(axis))}" for axis in controls
    )
    value_lists = [_axis_values(axis) for axis in controls]
    combos = list(itertools.product(*value_lists))

    return html.section(
        html.h2("Playground").class_("text-xl font-semibold text-surface-900"),
        html.p("Set props to preview combinations live.").class_(
            "text-sm text-surface-600"
        ),
        html.div(
            html.div(*[_combination_block(doc, controls, combo) for combo in combos]),
            _controls_table(controls),
        )
        .class_("space-y-3")
        .x_data(f"{{ sel: {{ {init} }} }}"),
    ).class_("space-y-4")
