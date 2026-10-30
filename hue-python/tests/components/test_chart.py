import json
import re
from pathlib import Path

import pytest

import hue
from hue.renderer import render_tree
from hue.ui import (
    AreaChart,
    BarChart,
    BubbleChart,
    DoughnutChart,
    LineChart,
    PieChart,
    ScatterChart,
)
from hue.ui.molecules.chart import _SWATCHES
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_DAYS = ["Mon", "Tue", "Wed"]


def _chart(cls: type[LineChart | AreaChart | BarChart] = LineChart):
    return (
        cls()
        .labels(_DAYS)
        .series([1200, 1500.5, 900], label="This week")
        .description("Revenue peaked on Tuesday.")
    )


def _spec(html: str) -> dict:
    x_data = select(html, "figure")[0]["x-data"]
    return json.loads(x_data.removeprefix("hueChart(").removesuffix(")"))


class TestSeriesCharts:
    @pytest.mark.asyncio
    async def test_the_table_is_the_text_alternative(self, context_args):
        # Captioned by the description, so the drawing stays silent rather
        # than saying it a second time.
        html = await render_tree(_chart(), context_args=context_args)
        assert_attr(html, "canvas", "aria-hidden", "true")
        # Hidden on a wrapper, since a table box does not shrink to 1px.
        assert_selector(html, "div.sr-only > table")
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

    @pytest.mark.parametrize(
        ("cls", "kind"), [(LineChart, "line"), (AreaChart, "area"), (BarChart, "bar")]
    )
    @pytest.mark.asyncio
    async def test_each_chart_draws_its_own_kind(self, context_args, cls, kind):
        spec = _spec(await render_tree(_chart(cls), context_args=context_args))
        assert spec["kind"] == kind
        # Only the currency format reads one.
        assert spec["y"] == {"format": "number", "currency": None}

    @pytest.mark.asyncio
    async def test_hands_the_series_to_the_loader(self, context_args):
        spec = _spec(await render_tree(_chart(), context_args=context_args))
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
        chart = LineChart().labels(['Say "hi"', "it's"]).series([1, 2], label='A "b"')
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
        chart = LineChart().labels(["a"]).series([0.5], label="s").description("x")
        html = await render_tree(
            chart.y_format(format_, currency="EUR"), context_args=context_args
        )
        assert select(html, "tbody td")[0].text == expected
        assert _spec(html)["y"]["format"] == format_

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

    @pytest.mark.parametrize(("label", "index"), [("Tue", 1), (None, None)])
    @pytest.mark.asyncio
    async def test_highlight_names_a_bar_by_its_label(self, context_args, label, index):
        chart = _chart(BarChart)
        if label is not None:
            chart = chart.highlight(label)
        spec = _spec(await render_tree(chart, context_args=context_args))
        assert spec["highlight"] == index

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

    @pytest.mark.parametrize(
        ("chart", "match"),
        [
            (LineChart().labels(["a"]).series([1], label="s"), "description"),
            (
                LineChart().labels(["a"]).series([1], label="s").description(" "),
                "description",
            ),
            (LineChart().labels(["a"]).description("x"), "series"),
            (LineChart().labels([]).series([], label="s").description("x"), "labels"),
            (
                _chart(BarChart).compare([1, 2, 3], label="b").highlight("Tue"),
                "highlight",
            ),
            (_chart().compare([1, 2], label="Last week"), "one value per label"),
            (_chart(BarChart).highlight("Sun"), "highlight"),
        ],
    )
    @pytest.mark.asyncio
    async def test_refuses_a_chart_it_cannot_draw(self, context_args, chart, match):
        with pytest.raises(ValueError, match=match):
            await render_tree(chart, context_args=context_args)

    @pytest.mark.parametrize("label", ["", "  "])
    def test_a_series_needs_a_label(self, label):
        with pytest.raises(ValueError, match="label"):
            LineChart().series([1], label=label)
        with pytest.raises(ValueError, match="label"):
            LineChart().compare([1], label=label)

    @pytest.mark.parametrize("code", ["usd ", "EURO", "€", ""])
    def test_rejects_a_malformed_currency(self, code):
        with pytest.raises(ValueError, match="ISO 4217"):
            LineChart().y_format("currency", currency=code)

    @pytest.mark.asyncio
    async def test_a_currency_code_is_upper_cased(self, context_args):
        chart = _chart().y_format("currency", currency="eur")
        assert (
            _spec(await render_tree(chart, context_args=context_args))["y"]["currency"]
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
        chart = LineChart().labels(["a"]).series([value], label="s").description("x")
        html = await render_tree(chart.y_format(format_), context_args=context_args)
        assert select(html, "tbody td")[0].text == expected

    @pytest.mark.parametrize("value", [float("nan"), float("inf")])
    def test_rejects_values_json_cannot_carry(self, value):
        with pytest.raises(ValueError, match="finite"):
            LineChart().series([value], label="s")


_SLICES = [("Paid", 92), ("Pending", 31), ("Draft", 14)]


def _pie() -> PieChart:
    return PieChart().slices(_SLICES).description("Most invoices are paid.")


class TestPieChart:
    @pytest.mark.asyncio
    async def test_draws_a_pie(self, context_args):
        spec = _spec(await render_tree(_pie(), context_args=context_args))
        assert spec["kind"] == "pie"
        assert spec["labels"] == ["Paid", "Pending", "Draft"]
        assert spec["series"][0]["values"] == [92, 31, 14]
        assert spec["series"][0]["display"] == ["92 (67%)", "31 (23%)", "14 (10%)"]
        doughnut = DoughnutChart().slices(_SLICES).description("x")
        assert (
            _spec(await render_tree(doughnut, context_args=context_args))["kind"]
            == "doughnut"
        )

    @pytest.mark.asyncio
    async def test_the_table_gives_each_slice_its_share(self, context_args):
        html = await render_tree(_pie(), context_args=context_args)
        assert [th.text for th in select(html, "thead th")] == ["Value", "Share"]
        assert [td.text for td in select(html, "tbody tr:first-child td")] == [
            "92",
            "67%",
        ]

    @pytest.mark.asyncio
    async def test_every_slice_has_a_swatch_in_the_legend(self, context_args):
        html = await render_tree(_pie(), context_args=context_args)
        assert [li.text for li in select(html, "figure > ul li")] == [
            "Paid",
            "Pending",
            "Draft",
        ]
        assert_selector(html, "figure > ul li:nth-child(2) span.bg-chart-2")

    @pytest.mark.asyncio
    async def test_past_six_slices_the_rest_are_grouped_as_other(self, context_args):
        slices = [(f"s{i}", n) for i, n in enumerate([5, 40, 1, 30, 2, 20, 10])]
        chart = PieChart().slices(slices).description("x")
        html = await render_tree(chart, context_args=context_args)
        spec = _spec(html)
        # The five largest in their own order, then the three smallest summed.
        assert spec["labels"] == ["s0", "s1", "s3", "s5", "s6", "Other"]
        assert spec["series"][0]["values"] == [5, 40, 30, 20, 10, 3]
        # The table still lists every slice.
        assert len(select(html, "tbody tr")) == 7
        assert_selector(html, "figure > ul li:last-child span.bg-chart-6")

    @pytest.mark.asyncio
    async def test_six_slices_are_all_drawn(self, context_args):
        slices = [(f"s{i}", 1) for i in range(6)]
        chart = PieChart().slices(slices).description("x")
        spec = _spec(await render_tree(chart, context_args=context_args))
        assert "Other" not in spec["labels"]

    @pytest.mark.parametrize(
        ("chart", "match"),
        [
            (PieChart().slices(_SLICES), "description"),
            (PieChart().description("x"), "total above zero"),
            (PieChart().slices([("a", 0)]).description("x"), "total above zero"),
            (DoughnutChart().description("x"), "DoughnutChart needs slices"),
        ],
    )
    @pytest.mark.asyncio
    async def test_refuses_a_pie_it_cannot_draw(self, context_args, chart, match):
        with pytest.raises(ValueError, match=match):
            await render_tree(chart, context_args=context_args)

    @pytest.mark.asyncio
    async def test_value_format_writes_values_and_keeps_the_share(self, context_args):
        chart = _pie().value_format("currency", currency="EUR")
        html = await render_tree(chart, context_args=context_args)
        assert _spec(html)["series"][0]["display"][0] == "92.00 EUR (67%)"
        assert [td.text for td in select(html, "tbody tr:first-child td")] == [
            "92.00 EUR",
            "67%",
        ]

    @pytest.mark.asyncio
    async def test_percent_values_are_not_followed_by_their_share(self, context_args):
        chart = PieChart().slices([("a", 0.25), ("b", 0.75)]).description("x")
        html = await render_tree(
            chart.value_format("percent"), context_args=context_args
        )
        assert _spec(html)["series"][0]["display"] == ["25%", "75%"]
        # Nor does the table give a Share column repeating them.
        assert [th.text for th in select(html, "thead th")] == ["Value"]
        assert [td.text for td in select(html, "tbody td")] == ["25%", "75%"]

    @pytest.mark.asyncio
    async def test_a_zero_slice_is_only_in_the_table(self, context_args):
        chart = PieChart().slices([("a", 3), ("b", 0)]).description("x")
        html = await render_tree(chart, context_args=context_args)
        assert _spec(html)["labels"] == ["a"]
        assert [li.text for li in select(html, "figure > ul li")] == ["a"]
        assert len(select(html, "tbody tr")) == 2

    @pytest.mark.parametrize(
        "numbers",
        # Seven slices group two as Other, which once rounded the rest anew.
        [[1, 1, 1], [2] * 7],
    )
    @pytest.mark.asyncio
    async def test_the_tooltip_and_the_table_give_a_slice_the_same_share(
        self, context_args, numbers
    ):
        slices = [(f"s{i}", n) for i, n in enumerate(numbers)]
        chart = PieChart().slices(slices).description("x")
        html = await render_tree(chart, context_args=context_args)
        table = {
            row.select("th")[0].text: row.select("td")[1].text
            for row in select(html, "tbody tr")
        }
        series = _spec(html)
        for label, text in zip(
            series["labels"], series["series"][0]["display"], strict=True
        ):
            if label != "Other":
                assert text.split("(")[1].rstrip(")") == table[label]

    @pytest.mark.parametrize(
        ("numbers", "shares"),
        [
            ([1, 1, 1], ["33%"] * 3),
            # Under half a percent reads under one, never as nothing.
            ([1, 1, 1, 297], ["<1%", "<1%", "<1%", "99%"]),
            ([999, 1], ["100%", "<1%"]),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_slice_reads_its_share(self, context_args, numbers, shares):
        slices = [(f"s{i}", n) for i, n in enumerate(numbers)]
        html = await render_tree(
            PieChart().slices(slices).description("x"), context_args=context_args
        )
        assert [row.select("td")[1].text for row in select(html, "tbody tr")] == shares

    @pytest.mark.asyncio
    async def test_a_slice_called_other_joins_the_grouped_one(self, context_args):
        slices = [("Other", 100), *((f"s{i}", 10 - i) for i in range(6))]
        chart = PieChart().slices(slices).description("x")
        spec = _spec(await render_tree(chart, context_args=context_args))
        assert spec["labels"] == ["s0", "s1", "s2", "s3", "s4", "Other"]
        assert spec["series"][0]["values"][-1] == 105

    @pytest.mark.parametrize(
        ("slices", "match"),
        [([("a", 1), ("a", 2)], "differ"), ([("a", -1)], "negative")],
    )
    def test_refuses_slices_it_cannot_draw(self, slices, match):
        with pytest.raises(ValueError, match=match):
            PieChart().slices(slices)


_POINTS = [(1, 2), (3, 4.5)]


def _scatter() -> ScatterChart:
    return (
        ScatterChart()
        .series(_POINTS, label="Orders")
        .x_label("Basket")
        .y_label("Margin")
        .description("Margin grows with basket size.")
    )


class TestScatterChart:
    @pytest.mark.asyncio
    async def test_hands_the_points_and_axes_to_the_loader(self, context_args):
        spec = _spec(await render_tree(_scatter(), context_args=context_args))
        assert spec["kind"] == "scatter"
        assert spec["series"][0]["points"] == [[1, 2], [3, 4.5]]
        # A line per value, which the tooltip stacks.
        assert spec["series"][0]["display"][1] == ["Basket: 3", "Margin: 4.5"]
        assert spec["x"]["label"] == "Basket"
        assert spec["y"]["label"] == "Margin"

    @pytest.mark.asyncio
    async def test_a_bubble_chart_has_a_size_column(self, context_args):
        chart = (
            BubbleChart()
            .series([(1, 2, 30)], label="Orders")
            .x_label("Basket")
            .y_label("Margin")
            .size_label("Customers")
            .description("x")
        )
        html = await render_tree(chart, context_args=context_args)
        assert _spec(html)["kind"] == "bubble"
        assert [th.text for th in select(html, "thead th")] == [
            "Basket",
            "Margin",
            "Customers",
        ]
        assert [td.text for td in select(html, "tbody td")] == ["1", "2", "30"]

    @pytest.mark.asyncio
    async def test_each_point_is_a_row_led_by_its_series(self, context_args):
        html = await render_tree(_scatter(), context_args=context_args)
        assert [th.text for th in select(html, "thead th")] == ["Basket", "Margin"]
        assert [th.text for th in select(html, "tbody th")] == ["Orders", "Orders"]

    @pytest.mark.asyncio
    async def test_a_second_series_adds_a_legend(self, context_args):
        chart = _scatter().series([(5, 6)], label="Returns")
        html = await render_tree(chart, context_args=context_args)
        assert [s["label"] for s in _spec(html)["series"]] == ["Orders", "Returns"]
        assert [li.text for li in select(html, "figure > ul li")] == [
            "Orders",
            "Returns",
        ]

    @pytest.mark.asyncio
    async def test_each_axis_has_its_own_format(self, context_args):
        chart = _scatter().x_format("currency", currency="EUR").y_format("percent")
        html = await render_tree(chart, context_args=context_args)
        spec = _spec(html)
        assert spec["x"]["format"] == "currency"
        assert spec["y"]["format"] == "percent"
        assert [td.text for td in select(html, "tbody tr:first-child td")] == [
            "1.00 EUR",
            "200%",
        ]

    @pytest.mark.asyncio
    async def test_a_bubble_size_is_a_plain_number(self, context_args):
        chart = (
            BubbleChart()
            .series([(1, 0.5, 1200)], label="s")
            .x_label("x")
            .y_label("y")
            .size_label("n")
            .y_format("percent")
            .description("d")
        )
        html = await render_tree(chart, context_args=context_args)
        assert [td.text for td in select(html, "tbody td")] == ["1", "50%", "1,200"]

    @pytest.mark.asyncio
    async def test_five_series_are_drawn(self, context_args):
        chart = _scatter()
        for i in range(4):
            chart = chart.series(_POINTS, label=f"s{i}")
        spec = _spec(await render_tree(chart, context_args=context_args))
        assert len(spec["series"]) == 5

    @pytest.mark.parametrize(
        ("chart", "match"),
        [
            (ScatterChart().x_label("x").y_label("y").description("d"), "series"),
            (
                ScatterChart().series(_POINTS, label="s").y_label("y").description("d"),
                "x_label",
            ),
            (
                BubbleChart()
                .series([(1, 2, 3)], label="s")
                .x_label("x")
                .y_label("y")
                .description("d"),
                "size_label",
            ),
            (
                ScatterChart()
                .x_label("x")
                .y_label("y")
                .description("d")
                .series(_POINTS, label="1")
                .series(_POINTS, label="2")
                .series(_POINTS, label="3")
                .series(_POINTS, label="4")
                .series(_POINTS, label="5")
                .series(_POINTS, label="6"),
                "at most 5",
            ),
            (_scatter().series(_POINTS, label="Orders"), "differ"),
        ],
    )
    @pytest.mark.asyncio
    async def test_refuses_a_scatter_it_cannot_draw(self, context_args, chart, match):
        with pytest.raises(ValueError, match=match):
            await render_tree(chart, context_args=context_args)

    @pytest.mark.parametrize(
        ("points", "match"),
        [
            ([], "at least one point"),
            ([(1,)], r"\(x, y\)"),
            # A size belongs on a BubbleChart.
            ([(1, 2, 3)], r"\(x, y\)"),
            ([(1, float("nan"))], "finite"),
        ],
    )
    def test_refuses_points_it_cannot_place(self, points, match):
        with pytest.raises(ValueError, match=match):
            ScatterChart().series(points, label="s")

    @pytest.mark.parametrize(
        ("points", "match"),
        [([(1, 2)], r"\(x, y, size\)"), ([(1, 2, -1)], "negative")],
    )
    def test_refuses_bubbles_it_cannot_place(self, points, match):
        with pytest.raises(ValueError, match=match):
            BubbleChart().series(points, label="s")


def test_every_swatch_is_a_token():
    # The legend's classes and the tokens chart-draw.js reads are named apart.
    # A --color-chart-N token is what gives bg-chart-N a colour.
    tokens = (
        Path(hue.__file__).parent / "static/styles/tailwind.input.css"
    ).read_text()
    for swatch in _SWATCHES:
        name = swatch.removeprefix("bg-")
        assert re.search(rf"--color-{name}:", tokens), swatch


@pytest.mark.asyncio
async def test_charts_of_every_kind_share_one_page(context_args):
    html = await render_tree(
        LineChart.example(),
        LineChart.example(),
        AreaChart.example(),
        BarChart.example(),
        PieChart.example(),
        DoughnutChart.example(),
        ScatterChart.example(),
        BubbleChart.example(),
        context_args=context_args,
    )
    assert_selector(html, "figure[x-data]", count=8)
    assert_no_selector(html, "[id]")


@pytest.mark.parametrize(
    ("chart", "floored"),
    [(LineChart.example(), False), (ScatterChart.example(), True)],
)
@pytest.mark.asyncio
async def test_only_point_charts_stop_shrinking(context_args, chart, floored):
    html = await render_tree(chart, context_args=context_args)
    # Out of flow, so its pixel width cannot hold a flex or grid cell open.
    assert_selector(html, "canvas.absolute.inset-0")
    assert bool(select(html, "div.min-h-48")) is floored
