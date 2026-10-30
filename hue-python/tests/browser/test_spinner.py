from htmy import html

from hue.ui import Spinner
from tests.browser.conftest import Show


def test_the_ring_stays_round_when_its_label_wraps(show: Show) -> None:
    spinner = Spinner().label("Loading every payment from the last financial year")
    page = show(html.div(spinner, style="width:120px"))
    # Its layout size, which turning it does not change.
    size = page.locator("[role=status] > span").first.evaluate(
        "ring => [ring.offsetWidth, ring.offsetHeight]"
    )
    assert size == [20, 20]
