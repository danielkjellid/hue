from __future__ import annotations

from collections.abc import Sequence

from htmy import Context, html
from typing_extensions import Self

from hue.toast import INHERIT, ToastMessage, ToastVariant, toast
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.spinner import Spinner
from hue.ui.base import ChainableComponent
from hue.ui.navigation import SYNC
from hue.utils import classnames, render_if, render_when

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

# A toast of one line centres its icon, title and dismiss button, which are
# taller than the title's line box; one with a description or an action keeps
# them on the first line. It is a CSS selector so that a toast $toast() clones
# from the template, then strips of its description and action, gets it too.
_ALIGN = "items-center has-[[data-toast-description],[data-toast-action]]:items-start"

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
    "{ ms: 0, timer: null, hovered: false, focused: false, "
    # A toast that arrives while the stack is scrolled back up would land out
    # of sight and time out unread, so the stack returns to the newest end,
    # which is scrollTop 0 because the stack is reversed. It stays put while a
    # pointer or focus is in it, since moving it would shift what someone is
    # reading or about to click, and the toast they are on is paused anyway.
    "init() { const region = this.$el.parentElement; "
    f"if (region?.id !== '{REGION_ID}') return; "
    "const stack = region.parentElement; "
    "if (!stack.matches(':hover') && !stack.contains(document.activeElement)) "
    "stack.scrollTo({ top: 0 }) }, "
    "start(ms) { this.stop(); "
    "if (ms) this.timer = setTimeout(() => this.dismiss(), ms) }, "
    "stop() { clearTimeout(this.timer); this.timer = null }, "
    "hold(why) { this[why] = true; this.stop() }, "
    # The pointer and the keyboard hold it separately, so a pointer passing
    # over a toast the keyboard is in does not set it leaving with focus
    # still inside. Only a toast that was leaving resumes: without that,
    # hovering one that was going to stay is what starts it counting down.
    "release(why) { this[why] = false; "
    "if (this.ms && !this.hovered && !this.focused) "
    f"this.start({_RESUME_MS}) }}, "
    # ms is cleared so the focusout the hand-off causes does not restart it.
    # Removing the focused toast would drop focus to the body, so it goes to
    # a neighbouring toast, then to where it was before it entered the
    # region, then to the region itself. A leaving toast turns inert, so a
    # second dismissal never hands focus to one already on its way out.
    "dismiss() { this.ms = 0; this.stop(); "
    "if ($el.contains(document.activeElement)) "
    "$handOff($el, { within: $el.parentElement, "
    "returnTo: $el.parentElement._hueReturn, fallback: $el.parentElement }); "
    "$el.inert = true; $el.classList.add('animate-toast-out'); "
    "setTimeout(() => $el.remove(), 180) }, "
    "enter(from) { this.hold('focused'); "
    "if (from && !$el.parentElement.contains(from)) "
    "$el.parentElement._hueReturn = from } }"
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

    def _render(self, context: Context) -> Component:
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
                # The height of the title's line, so the icon sits on it.
                class_=classnames("flex h-5 flex-none items-center", _TONES[variant]),
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
                "pointer-events-auto flex gap-3 rounded-lg border",
                _ALIGN,
                "border-border bg-surface-raised px-4 py-3 shadow-overlay",
                "animate-toast-in",
                self._get_prop("class_"),
            ),
            **{
                "x-data": _TIMER,
                "x-init": _init(self, variant),
                "x-on:mouseenter": "hold('hovered')",
                "x-on:mouseleave": "release('hovered')",
                "x-on:focusin": "enter($event.relatedTarget)",
                "x-on:focusout": (
                    "if (!$el.contains($event.relatedTarget)) release('focused')"
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
        start = f"ms = $data.{_DEFAULT} ?? 0; start(ms)"
    else:
        duration: int | None = toast._get_prop("duration")
        start = f"ms = {duration if duration is not None else 0}; start(ms)"
    if variant != "danger":
        return start
    return f"{start}; $data.announce?.($el.innerText.trim())"


class ToastRegion(ChainableComponent):
    """
    Where toasts arrive, placed once in the page base.

    A live region that exists before anything is in it, because one created
    together with its content is never read out. Toasts sent from the server
    are merged into it by their id, and $toast() builds one from the
    templates it carries. default_duration() sets how long they stay.
    """

    category = None

    def default_duration(self, value: int) -> Self:
        """
        Milliseconds a toast in this region stays, for the ones that do not
        set their own. 5200 by default, which is the time it takes to read
        two short lines twice.
        """
        self._props["default_duration"] = value
        return self

    def _render(self, context: Context) -> Component:
        # Whatever the handler queued is rendered here, which is also what
        # keeps the router from appending it a second time.
        return html.div(
            # A stack taller than the window scrolls rather than running off
            # its top, so every toast stays reachable by pointer, touch and
            # Tab. Reversed around its one child, which starts the scroll at
            # the bottom and keeps it there as toasts arrive, without
            # changing the reading order. The gutter is padding rather than
            # an inset, so the toasts' shadows are not clipped.
            html.div(
                html.div(
                    *(_template(variant) for variant in _ICONS),
                    *(from_message(message) for message in toast.drain()),
                    id=REGION_ID,
                    # x-sync puts this element in the targets of every Alpine
                    # AJAX request, so a toast raised by any handler finds its
                    # way here; append rather than replace, so the ones
                    # already on screen stay.
                    **{**SYNC, "x-merge": "append"},
                    aria_live="polite",
                    class_="flex flex-col gap-2",
                ),
                class_=classnames(
                    "pointer-events-none fixed inset-x-0 bottom-0 z-90 flex",
                    "max-h-dvh flex-col-reverse overflow-y-auto p-4",
                    "sm:inset-x-auto sm:end-0 sm:p-6",
                    "sm:w-[calc(min(380px,100vw-2rem)+3rem)]",
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
                f"{self._get_prop('default_duration', _DURATION_MS)}, "
                "announce(text) { "
                "this.$refs.announcer.textContent = ''; "
                "this.$refs.announcer.textContent = text } }",
                **self._get_base_html_attrs(),
            },
        )


def from_message(message: ToastMessage) -> Toast:
    """
    The component for a toast a handler queued.
    """
    built = (
        Toast()
        .variant(message.variant)
        .title(message.title)
        .dismissible(message.dismissible)
    )
    render_if(message.description, built.description)
    render_if(message.action, built.action)
    if message.duration is not INHERIT:
        built.duration(message.duration)
    return built


def region_fragment(messages: Sequence[ToastMessage]) -> ComponentType:
    """
    Just the toasts, under the region's id.

    Alpine AJAX merges this into the live region by that id and appends its
    children, so a toast raised by any handler reaches the page it came from
    without the caller targeting anything.
    """
    return html.div(*(from_message(message) for message in messages), id=REGION_ID)


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
