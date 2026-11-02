"""
The view every page of the example inherits, for the shell it draws.
"""

from django.http import HttpRequest
from django.urls import reverse
from hue import html
from hue.context import HueContext
from hue.types.core import ComponentType
from hue.ui import (
    Badge,
    Sidebar,
    SidebarBody,
    SidebarItem,
    SidebarLabel,
    SidebarSection,
    ToastRegion,
)
from hue_django.views import HueView

from example.invoices.models import Invoice


class AppView(HueView):
    def layout(
        self, body: ComponentType, context: HueContext[HttpRequest]
    ) -> ComponentType:
        """
        The sidebar beside the page, and the one toast region a page needs.

        Sync on purpose: hue runs a sync layout off the event loop, as it does
        a sync view, so the count below may query the database.
        """
        pending = Invoice.objects.filter(
            archived=False, status=Invoice.Status.PENDING
        ).count()
        return (
            html.div()
            .class_("example-shell")
            .content(
                Sidebar()
                .current(context.request.path)
                .content(
                    SidebarBody().content(
                        SidebarSection().content(
                            SidebarItem()
                            .href(reverse("invoicesview:index"))
                            .content(
                                SidebarLabel().content("Invoices"),
                                Badge().variant("warning").content(str(pending)),
                            ),
                            SidebarItem()
                            .href(reverse("eventsview:index"))
                            .content("Events"),
                        )
                    )
                ),
                html.main().class_("example-page").content(body),
                # Once per page, and there before the first toast: a live
                # region made together with its content is not read out.
                ToastRegion(),
            )
        )
