import json

import pytest

from hue.renderer import render_tree
from hue.ui import Chart
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_DAYS = ["Mon", "Tue", "Wed"]


def _chart() -> Chart:
    return (
        Chart()
        .labels(_DAYS)
        .series([1200, 1500.5, 900], label="This week")
        .description("Revenue peaked on Tuesday.")
    )


def _spec(html: str) -> dict:
    x_data = select(html, "figure")[0]["x-data"]
    return json.loads(x_data.removeprefix("hueChart(").removesuffix(")"))


class TestChart:
    @pytest.mark.asyncio
    async def test_the_table_is_the_text_alternative(self, context_args):
        # Captioned by the description, so the drawing stays silent rather
        # than saying it a second time.
        html = await render_tree(_chart(), context_args=context_args)
        assert_attr(html, "canvas", "aria-hidden", "true")
        assert_selector(html, "table.sr-only")
        caption = select(html, "table caption")[0].text.strip()
        assert caption == "Revenue peaked on Tuesday."
        # And it names the figure, where focus lands after a retry.
        assert_attr(html, "table caption", ":id", "$id('hue-chart-caption')")
        assert_attr(html, "figure", ":aria-labelledby", "$id('hue-chart-caption')")
        assert [th.text for th in select(html, "thead th")] == ["This week"]
        assert [th.text for th in select(html, "tbody th[scope=row]")] == _DAYS
        assert [td.text for td in select(html, "tbody td")] == [
            "1,200",
            "1,500.5",
            "900",
        ]

    @pytest.mark.asyncio
    async def test_the_default_kind_is_area(self, context_args):
        spec = _spec(await render_tree(_chart(), context_args=context_args))
        assert spec["kind"] == "area"
        # Only the currency format reads one.
        assert spec["currency"] is None

    @pytest.mark.asyncio
    async def test_hands_the_series_to_the_loader(self, context_args):
        spec = _spec(await render_tree(_chart().kind("bar"), context_args=context_args))
        assert spec["kind"] == "bar"
        assert spec["labels"] == _DAYS
        assert spec["series"] == [
            {
                "label": "This week",
                "values": [1200, 1500.5, 900],
                "display": ["1,200", "1,500.5", "900"],
            }
        ]

    @pytest.mark.asyncio
    async def test_text_with_quotes_survives_the_expression(self, context_args):
        chart = Chart().labels(['Say "hi"', "it's"]).series([1, 2], label='A "b"')
        html = await render_tree(chart.description("x"), context_args=context_args)
        spec = _spec(html)
        assert spec["labels"] == ['Say "hi"', "it's"]
        assert spec["series"][0]["label"] == 'A "b"'

    @pytest.mark.parametrize(
        ("format_", "expected"),
        [("number", "0.5"), ("percent", "50%"), ("currency", "0.50 EUR")],
    )
    @pytest.mark.asyncio
    async def test_y_format_writes_the_values(self, context_args, format_, expected):
        chart = Chart().labels(["a"]).series([0.5], label="s").description("x")
        html = await render_tree(
            chart.y_format(format_, currency="EUR"), context_args=context_args
        )
        assert select(html, "tbody td")[0].text == expected
        assert _spec(html)["format"] == format_

    @pytest.mark.asyncio
    async def test_compare_adds_a_second_series_and_a_legend(self, context_args):
        chart = _chart().compare([1, 2, 3], label="Last week")
        html = await render_tree(chart, context_args=context_args)
        assert [s["label"] for s in _spec(html)["series"]] == ["This week", "Last week"]
        assert [li.text for li in select(html, "figure > ul li")] == [
            "This week",
            "Last week",
        ]
        assert [th.text for th in select(html, "thead th")] == [
            "This week",
            "Last week",
        ]

    @pytest.mark.asyncio
    async def test_a_single_series_has_no_legend(self, context_args):
        html = await render_tree(_chart(), context_args=context_args)
        assert_no_selector(html, "figure > ul")

    @pytest.mark.asyncio
    async def test_highlight_names_a_bar_by_its_label(self, context_args):
        chart = _chart().kind("bar").highlight("Tue")
        assert (
            _spec(await render_tree(chart, context_args=context_args))["highlight"] == 1
        )

    @pytest.mark.asyncio
    async def test_nothing_is_highlighted_by_default(self, context_args):
        chart = _chart().kind("bar")
        assert (
            _spec(await render_tree(chart, context_args=context_args))["highlight"]
            is None
        )

    @pytest.mark.asyncio
    async def test_the_retry_overlay_waits_for_a_failure(self, context_args):
        html = await render_tree(_chart(), context_args=context_args)
        assert_attr(html, "figure [hidden]", ":hidden", "!failed")
        assert_attr(html, "figure [hidden] button", "@click", "retry()")
        assert_attr(html, "figure [hidden] button", "x-ref", "retry")
        assert_attr(
            html,
            "figure [hidden] button",
            ":aria-describedby",
            "$id('hue-chart-error')",
        )
        assert_attr(html, "figure [hidden] p", ":id", "$id('hue-chart-error')")
        # Where focus goes when Retry hides itself.
        assert_attr(html, "figure", "tabindex", "-1")

    @pytest.mark.asyncio
    async def test_two_charts_render_on_one_page(self, context_args):
        html = await render_tree(
            Chart.example(), Chart.example(), context_args=context_args
        )
        assert_selector(html, "figure[x-data]", count=2)
        assert_no_selector(html, "[id]")

    @pytest.mark.parametrize(
        ("chart", "match"),
        [
            (Chart().labels(["a"]).series([1], label="s"), "description"),
            (
                Chart().labels(["a"]).series([1], label="s").description(" "),
                "description",
            ),
            (Chart().labels(["a"]).description("x"), "series"),
            (Chart().labels([]).series([], label="s").description("x"), "labels"),
            (
                _chart().kind("bar").compare([1, 2, 3], label="b").highlight("Tue"),
                "highlight",
            ),
            (_chart().compare([1, 2], label="Last week"), "one value per label"),
            (_chart().kind("line").highlight("Tue"), "highlight"),
            (_chart().kind("bar").highlight("Sun"), "highlight"),
        ],
    )
    @pytest.mark.asyncio
    async def test_refuses_a_chart_it_cannot_draw(self, context_args, chart, match):
        with pytest.raises(ValueError, match=match):
            await render_tree(chart, context_args=context_args)

    @pytest.mark.parametrize("label", ["", "  "])
    def test_a_series_needs_a_label(self, label):
        with pytest.raises(ValueError, match="label"):
            Chart().series([1], label=label)
        with pytest.raises(ValueError, match="label"):
            Chart().compare([1], label=label)

    @pytest.mark.parametrize("code", ["usd ", "EURO", "€", ""])
    def test_rejects_a_malformed_currency(self, code):
        with pytest.raises(ValueError, match="ISO 4217"):
            Chart().y_format("currency", currency=code)

    @pytest.mark.asyncio
    async def test_a_currency_code_is_upper_cased(self, context_args):
        chart = _chart().y_format("currency", currency="eur")
        assert (
            _spec(await render_tree(chart, context_args=context_args))["currency"]
            == "EUR"
        )

    @pytest.mark.parametrize(
        ("format_", "value", "expected"),
        [
            ("number", 0, "0"),
            # A small negative rounds to zero rather than to "-0".
            ("number", -0.001, "0"),
            ("currency", -0.001, "0.00 USD"),
        ],
    )
    @pytest.mark.asyncio
    async def test_zero_is_written_as_zero(
        self, context_args, format_, value, expected
    ):
        chart = Chart().labels(["a"]).series([value], label="s").description("x")
        html = await render_tree(chart.y_format(format_), context_args=context_args)
        assert select(html, "tbody td")[0].text == expected

    @pytest.mark.parametrize("value", [float("nan"), float("inf")])
    def test_rejects_values_json_cannot_carry(self, value):
        with pytest.raises(ValueError, match="finite"):
            Chart().series([value], label="s")
