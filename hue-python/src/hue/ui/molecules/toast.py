from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.spinner import Spinner
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

type ToastVariant = Literal["success", "danger", "warning", "info", "loading"]

#: The id the region answers to. Every toast that arrives from the server is
#: merged into this element, so there is one per page and it is named here
#: rather than passed around.
REGION_ID = "hue-toasts"
ANNOUNCER_ID = "hue-toast-announcer"

# 5.2s to read it, and 2.6s once a pointer that paused it leaves again - the
# second timer is shorter because the toast has already been on screen.
_DURATION_MS = 5200
_RESUME_MS = 2600

# The name the region's default hangs off in the Alpine scope every toast
# inside it inherits. Prefixed, because that scope is the consumer's page.
_DEFAULT = "hueToastDuration"

_ICONS: dict[ToastVariant, str] = {
    "success": "circle-check",
    "danger": "circle-x",
    "warning": "triangle-alert",
    "info": "circle-info",
    "loading": "",
}

_TONES: dict[ToastVariant, str] = {
    "success": "text-success",
    "danger": "text-danger",
    "warning": "text-warning",
    "info": "text-info",
    "loading": "text-fg-subtle",
}

# Its own timer, because a toast arrives on its own and has to leave on its
# own. Pausing on hover and on focus is WCAG 2.2.1: an auto-dismissing
# message has to be stoppable by whoever is still reading it.
_TIMER = (
    "{ timer: null, "
    "start(ms) { this.stop(); "
    "if (ms) this.timer = setTimeout(() => this.dismiss(), ms) }, "
    "stop() { clearTimeout(this.timer) }, "
    "dismiss() { this.stop(); "
    "$el.classList.add('animate-toast-out'); "
    "setTimeout(() => $el.remove(), 180) } }"
)


class Toast(ChainableComponent):
    """
    A transient note about something that just happened.

    It lives in a ToastRegion, which is what announces it and what times it;
    on its own it is only the card, and stays. In a region it leaves after
    the region's five seconds unless a pointer or the keyboard is on it, and
    duration(None) keeps it until it is dismissed.
    Never put the only way out of a problem in one - that belongs in an Alert
    that stays.
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("success")
            .title("Invoice sent")
            .description("INV-2048 sent to ada@example.com")
        )

    def variant(self, value: ToastVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def action(self, *values: ComponentType) -> Self:
        """
        One way to follow up on it, under the text. A second chance at the
        thing that failed, not the only chance.
        """
        self._props["action"] = values
        return self

    def duration(self, value: int | None) -> Self:
        """
        Milliseconds on screen, or None to stay until it is dismissed. Unset,
        it takes the region's default.
        """
        self._props["duration"] = value
        return self

    def dismissible(self, value: bool = True) -> Self:
        self._props["dismissible"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ToastVariant = self._get_prop("variant", "info")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        action: tuple[ComponentType, ...] = self._get_prop("action", ())
        dismissible: bool = self._get_prop("dismissible", True)

        icon: ComponentType = (
            Spinner().size("sm").muted()
            if variant == "loading"
            else HueIcon(_ICONS[variant]).class_("size-4")
        )

        return html.div(
            html.span(
                icon,
                aria_hidden="true",
                class_=classnames("mt-px flex-none", _TONES[variant]),
            ),
            html.div(
                render_if(
                    title,
                    lambda text: html.div(
                        text,
                        class_="font-ui text-base font-medium leading-[1.4] text-fg",
                        data_toast_title="",
                    ),
                ),
                render_if(
                    description,
                    lambda text: html.div(
                        text,
                        class_="mt-px text-sm leading-[1.45] text-fg-muted",
                        data_toast_description="",
                    ),
                ),
                render_when(
                    bool(action),
                    html.div(*action, class_="mt-2", data_toast_action=""),
                ),
                class_="min-w-0 flex-1",
            ),
            render_when(
                dismissible,
                html.button(
                    HueIcon("x").class_("size-3.5"),
                    type="button",
                    aria_label="Dismiss",
                    class_=classnames(
                        "grid size-6 flex-none place-content-center rounded-sm",
                        "cursor-pointer text-fg-subtle hover:bg-surface-hover "
                        "hover:text-fg",
                        FOCUS_RING,
                    ),
                    **{"x-on:click": "dismiss()"},
                ),
            ),
            class_=classnames(
                "pointer-events-auto flex items-start gap-3 rounded-lg border",
                "border-border bg-surface-raised px-4 py-3 shadow-overlay",
                "animate-toast-in",
                self._get_prop("class_"),
            ),
            **{
                "x-data": _TIMER,
                "x-init": _init(self, variant),
                "x-on:mouseenter": "stop()",
                "x-on:mouseleave": f"start({_RESUME_MS})",
                "x-on:focusin": "stop()",
                "x-on:focusout": (
                    f"if (!$el.contains($event.relatedTarget)) start({_RESUME_MS})"
                ),
                **self._get_base_html_attrs(),
            },
        )


def _init(toast: Toast, variant: ToastVariant) -> str:
    """
    Start the timer, and for a failure also write the text into the region's
    assertive announcer - polite means "when you get a moment", and a failure
    cannot wait for one.

    The text is read off the element rather than written in here, so a toast
    the browser cloned from a template announces what it actually says. Via
    $data, because a toast rendered outside a region has nothing to announce
    into.
    """
    # Unset, the toast asks the region it is in - and outside one there is no
    # timer at all, because the region is what times a toast. A specimen on a
    # page is then a card that stays put rather than one that quietly leaves.
    if "duration" not in toast._props:
        start = f"start($data.{_DEFAULT} ?? 0)"
    else:
        duration: int | None = toast._get_prop("duration")
        start = f"start({duration if duration is not None else 0})"
    if variant != "danger":
        return start
    return f"{start}; $data.announce?.($el.innerText.trim())"


class ToastRegion(ChainableComponent):
    """
    Where toasts arrive, placed once in the page base.

    A live region that exists before anything is in it, because one created
    together with its content is never read out. Toasts sent from the server
    are merged into it by their id, and $toast() builds one from the
    templates it carries. duration() sets how long they stay.
    """

    category = None

    def duration(self, value: int) -> Self:
        """
        Milliseconds a toast in this region stays, for the ones that do not
        set their own. 5200 by default, which is the time it takes to read
        two short lines twice.
        """
        self._props["duration"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        return html.div(
            html.div(
                *(_template(variant) for variant in _ICONS),
                id=REGION_ID,
                # x-sync puts this element in the targets of every Alpine AJAX
                # request, so a toast raised by any handler finds its way
                # here; append rather than replace, so the ones already on
                # screen stay.
                **{"x-sync": True, "x-merge": "append"},
                aria_live="polite",
                class_=classnames(
                    "pointer-events-none fixed inset-x-4 bottom-4 z-90 flex",
                    "flex-col gap-2",
                    "sm:inset-x-auto sm:end-6 sm:bottom-6",
                    "sm:w-[min(380px,calc(100vw-2rem))]",
                ),
            ),
            # Assertive and empty, waiting for a failure to be written into
            # it. Outside the polite region: a live region inside another one
            # is read by neither reliably.
            html.div(
                id=ANNOUNCER_ID, role="alert", class_="sr-only", x_ref="announcer"
            ),
            class_=self._get_prop("class_"),
            **{
                "x-data": f"{{ {_DEFAULT}: "
                f"{self._get_prop('duration', _DURATION_MS)}, "
                "announce(text) { "
                "this.$refs.announcer.textContent = ''; "
                "this.$refs.announcer.textContent = text } }",
                **self._get_base_html_attrs(),
            },
        )


def _template(variant: ToastVariant) -> ComponentType:
    """
    The markup $toast() clones for one variant.

    A template rather than markup built in JavaScript, so a toast raised on
    the client is the same element as one raised on the server, down to the
    class list.
    """
    return html.template(
        Toast()
        .variant(variant)
        .title("")
        .description("")
        .action(Button().variant("outline").size("xs")),
        data_variant=variant,
    )
