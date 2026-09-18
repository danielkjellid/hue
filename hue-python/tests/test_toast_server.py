from unittest.mock import Mock

import pytest
from htmy import html

from hue.context import HueContext
from hue.renderer import render_tree
from hue.toast import INHERIT, ToastMessage, toast
from hue.types.core import Component
from hue.ui import ToastRegion
from tests.conftest import MockRequest, MockRouter


def _view(*, raises: bool):
    def view_func(
        view_instance: object,
        request: MockRequest,
        context: HueContext[MockRequest],
    ) -> Component:
        if raises:
            toast.success("Invoice sent", description="INV-2048 to ada@example.com")
        return html.div("Fragment")

    return view_func


class TestQueue:
    def test_a_toast_needs_a_request_to_carry_it(self):
        # Silently dropping it would be worse than saying so.
        with pytest.raises(RuntimeError, match="no request to carry it"):
            toast.success("Nowhere to go")

    def test_draining_takes_everything_and_leaves_nothing(self):
        token = toast.open()
        try:
            toast.success("One")
            toast.danger("Two", duration=None)
            taken = toast.drain()
            assert [message.title for message in taken] == ["One", "Two"]
            assert [message.variant for message in taken] == ["success", "danger"]
            assert taken[0].duration is INHERIT
            assert taken[1].duration is None
            assert toast.drain() == []
        finally:
            toast.close(token)

    def test_one_request_cannot_see_another(self):
        first = toast.open()
        toast.success("Mine")
        toast.close(first)

        second = toast.open()
        try:
            assert toast.drain() == []
        finally:
            toast.close(second)


class TestStoring:
    def test_a_message_survives_a_round_trip_as_data(self):
        token = toast.open()
        try:
            toast.info("Saved", description="Three fields changed")
            toast.warning("Careful", duration=2000, dismissible=False)
            stored = [message.as_dict() for message in toast.drain()]
        finally:
            toast.close(token)

        first, second = (ToastMessage.from_dict(data) for data in stored)
        assert (first.variant, first.title, first.description) == (
            "info",
            "Saved",
            "Three fields changed",
        )
        # Unset stays unset rather than becoming a number of its own.
        assert first.duration is INHERIT
        assert (second.duration, second.dismissible) == (2000, False)

    def test_an_action_cannot_be_stored(self):
        # It is a component, not data, and losing the button quietly on the
        # way through a redirect would be worse than saying so.
        message = ToastMessage(variant="danger", title="Failed", action=object())
        with pytest.raises(TypeError, match="cannot be stored"):
            message.as_dict()

    def test_restored_messages_come_before_the_ones_raised_since(self):
        token = toast.open()
        try:
            toast.success("Raised now")
            toast.restore([ToastMessage(variant="info", title="From before")])
            assert [message.title for message in toast.drain()] == [
                "From before",
                "Raised now",
            ]
        finally:
            toast.close(token)

    def test_a_queue_that_is_already_open_is_left_to_its_owner(self):
        # A middleware opens one for the whole request; the router nests
        # inside it rather than shadowing it, or a flashed toast would be
        # invisible to the page that was meant to show it.
        outer = toast.open()
        try:
            toast.restore([ToastMessage(variant="info", title="From before")])
            inner = toast.open()
            assert inner is None
            toast.success("Raised in the handler")
            toast.close(inner)
            assert [message.title for message in toast.drain()] == [
                "From before",
                "Raised in the handler",
            ]
        finally:
            toast.close(outer)


class TestRendering:
    @pytest.mark.asyncio
    async def test_a_page_renders_its_own_into_the_region(
        self, context_args, router: MockRouter, mock_request: type[MockRequest]
    ):
        token = toast.open()
        try:
            toast.warning("Careful", description="That was close")
            html_result = await render_tree(ToastRegion(), context_args=context_args)
            assert "Careful" in html_result
            assert "That was close" in html_result
            # And the region emptying the queue is what keeps the router from
            # sending the same toast a second time.
            assert toast.drain() == []
        finally:
            toast.close(token)

    @pytest.mark.asyncio
    async def test_a_fragment_carries_its_toasts_behind_it(
        self, router: MockRouter, mock_request: type[MockRequest]
    ):
        wrapped = router._wrap_view(_view(raises=True), require_ajax=True)
        request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
        html_result, _ = await wrapped(Mock(), request)

        assert "Fragment" in html_result
        assert 'id="hue-toasts"' in html_result
        assert "Invoice sent" in html_result

    @pytest.mark.asyncio
    async def test_a_fragment_that_raised_none_carries_nothing(
        self, router: MockRouter, mock_request: type[MockRequest]
    ):
        wrapped = router._wrap_view(_view(raises=False), require_ajax=True)
        request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
        html_result, _ = await wrapped(Mock(), request)

        assert "Fragment" in html_result
        assert "hue-toasts" not in html_result

    @pytest.mark.asyncio
    async def test_a_toast_does_not_survive_into_the_next_request(
        self, router: MockRouter, mock_request: type[MockRequest]
    ):
        request = mock_request(headers={"X-Requested-With": "XMLHttpRequest"})
        raised = router._wrap_view(_view(raises=True), require_ajax=True)
        await raised(Mock(), request)

        quiet = router._wrap_view(_view(raises=False), require_ajax=True)
        html_result, _ = await quiet(Mock(), request)
        assert "Invoice sent" not in html_result
