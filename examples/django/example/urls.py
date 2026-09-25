from django.urls import include, path
from django.views.generic import RedirectView

from example.invoices.views import InvoicesView

# Under a prefix on purpose: a table that spelled its own paths would be right
# until the first include(), and this is the include().
urlpatterns = [
    path("", RedirectView.as_view(url="/billing/")),
    path("billing/", include(InvoicesView.urls)),
]
