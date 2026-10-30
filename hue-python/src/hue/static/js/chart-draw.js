/**
 * Entry point for chart-bundle.js, which chart-loader.js fetches. It registers
 * only the chart types hue's chart components draw, so the rest of Chart.js
 * stays out.
 *
 * draw() takes the spec a chart component renders and turns it into a
 * Chart.js config, with every colour read from the design tokens at the time
 * it is called. A canvas cannot follow a CSS variable on its own, so the
 * loader calls draw() again when the theme changes.
 */
import {
	ArcElement,
	BarController,
	BarElement,
	BubbleController,
	CategoryScale,
	Chart,
	DoughnutController,
	Filler,
	LinearScale,
	LineController,
	LineElement,
	PieController,
	PointElement,
	ScatterController,
	Tooltip,
} from "chart.js";

Chart.register(
	ArcElement,
	BarController,
	BarElement,
	BubbleController,
	CategoryScale,
	DoughnutController,
	Filler,
	LinearScale,
	LineController,
	LineElement,
	PieController,
	PointElement,
	ScatterController,
	Tooltip,
);

// Resolved through elements rather than read off the custom properties, so a
// token that is itself a color-mix() arrives as a colour the canvas can use.
// All of them are read in one pass, which costs one style recalculation
// rather than one per colour.
function resolve(canvas, colors) {
	const probes = Object.values(colors).map((color) => {
		const probe = document.createElement("span");
		probe.style.color = color;
		return probe;
	});
	canvas.parentElement.append(...probes);
	const resolved = probes.map((probe) => getComputedStyle(probe).color);
	for (const probe of probes) probe.remove();
	return Object.fromEntries(Object.keys(colors).map((name, i) => [name, resolved[i]]));
}

// The components' legends name the same chart-N tokens for their swatches.
function palette(canvas) {
	const vivid = (percent) =>
		`color-mix(in srgb, var(--color-accent-vivid) ${percent}%, transparent)`;
	const colors = resolve(canvas, {
		chart1: "var(--color-chart-1)",
		chart2: "var(--color-chart-2)",
		chart3: "var(--color-chart-3)",
		chart4: "var(--color-chart-4)",
		chart5: "var(--color-chart-5)",
		chart6: "var(--color-chart-6)",
		axis: "var(--color-fg-subtle)",
		grid: "var(--color-border)",
		surface: "var(--color-surface)",
		tooltip: "var(--color-fg-strong)",
		tooltipText: "var(--color-canvas)",
		areaTop: vivid(24),
		areaBottom: vivid(0),
	});
	colors.series = [1, 2, 3, 4, 5, 6].map((n) => colors[`chart${n}`]);
	return colors;
}

function numberFormat({ format, currency }) {
	// English, with a currency's code after the number, like the values the
	// components write for the tooltip and the table, so the axis does not
	// group digits or mark money differently from them.
	const compact = new Intl.NumberFormat("en", {
		notation: "compact",
		style: format === "percent" ? "percent" : "decimal",
	});
	return format === "currency"
		? (value) => `${compact.format(value)} ${currency}`
		: (value) => compact.format(value);
}

function valueAxis(theme, format, extra = {}) {
	return {
		grid: { color: theme.colors.grid },
		border: { display: false },
		ticks: { ...theme.ticks, maxTicksLimit: 5, callback: numberFormat(format) },
		title: format.label
			? { display: true, text: format.label, color: theme.colors.axis, font: theme.ticks.font }
			: undefined,
		...extra,
	};
}

// Line, area and bar: one value per label, the main series in the accent and
// a comparison muted.
function categoryConfig(spec, theme) {
	const { colors } = theme;
	const accent = colors.series[0];
	const muted = colors.series[5];

	const dataset = (series, index) => {
		const main = index === 0;
		if (spec.kind === "bar") {
			return {
				label: series.label,
				data: series.values,
				backgroundColor: main
					? series.values.map((_, i) =>
							spec.highlight === null || spec.highlight === i ? accent : muted,
						)
					: muted,
				borderRadius: 3,
				maxBarThickness: 44,
			};
		}
		const color = main ? accent : muted;
		const last = series.values.length - 1;
		return {
			label: series.label,
			data: series.values,
			borderColor: color,
			borderWidth: main ? 2 : 1.5,
			borderDash: main ? [] : [4, 4],
			// Only the latest point is marked, which is also what keeps a series
			// of one value from drawing nothing at all.
			pointRadius: (context) => (context.dataIndex === last ? 4 : 0),
			pointBackgroundColor: colors.surface,
			pointBorderColor: color,
			pointBorderWidth: 2,
			fill: main && spec.kind === "area" ? "origin" : false,
			backgroundColor(context) {
				const { chartArea, ctx } = context.chart;
				if (!chartArea) return colors.areaBottom;
				const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
				gradient.addColorStop(0, colors.areaTop);
				gradient.addColorStop(1, colors.areaBottom);
				return gradient;
			},
		};
	};

	return {
		type: spec.kind === "bar" ? "bar" : "line",
		data: {
			labels: spec.labels,
			// Chart.js paints the first dataset last, so the main series sits on
			// top of its comparison.
			datasets: spec.series.map(dataset),
		},
		options: {
			interaction: { mode: "index", intersect: false },
			scales: {
				x: {
					grid: { display: false },
					border: { display: false },
					// Bars tilt their labels to fit as many as they can, and skip
					// only what still would not fit, since overlapping labels name
					// nothing. The padding keeps tilted lines a line height apart.
					// The tooltip and the table name every bar either way.
					ticks:
						spec.kind === "bar"
							? { ...theme.ticks, maxRotation: 90, autoSkipPadding: 3 }
							: { ...theme.ticks, maxRotation: 0, autoSkipPadding: 16 },
				},
				y: valueAxis(theme, spec.y, { beginAtZero: true }),
			},
		},
		label: ({ datasetIndex, dataIndex }) => {
			const series = spec.series[datasetIndex];
			return `${series.label}: ${series.display[dataIndex]}`;
		},
		// Chart.js takes a line's swatch from its point, which is hollow, so
		// it is filled with the line's colour to match the legend.
		swatch:
			spec.kind === "bar"
				? undefined
				: ({ dataset }) => ({
						borderColor: dataset.borderColor,
						backgroundColor: dataset.borderColor,
					}),
	};
}

// Pie and doughnut: one series, a colour per slice, with a gap of surface
// between slices so neighbours stay apart even where colours are close.
function pieConfig(spec, theme) {
	const [series] = spec.series;
	return {
		type: spec.kind,
		data: {
			labels: spec.labels,
			datasets: [
				{
					data: series.values,
					backgroundColor: theme.colors.series,
					borderColor: theme.colors.surface,
					// One slice has no neighbour, and its border would draw a
					// seam from the centre.
					borderWidth: series.values.length > 1 ? 2 : 0,
					hoverOffset: 4,
				},
			],
		},
		options: {},
		// The tooltip's title already names the slice.
		label: ({ dataIndex }) => series.display[dataIndex],
	};
}

// Scatter and bubble: numeric points, a colour per series. A bubble's area
// follows its size, scaled against the largest on the chart.
function pointConfig(spec, theme) {
	const largest = Math.max(0, ...spec.series.flatMap((s) => s.points.map((p) => p[2] ?? 0)));
	const radius = (size) => 3 + (largest ? 17 * Math.sqrt(size / largest) : 0);

	return {
		type: spec.kind,
		data: {
			datasets: spec.series.map((series, index) => ({
				label: series.label,
				data: series.points.map(([x, y, size]) => ({ x, y, r: radius(size ?? 0) })),
				backgroundColor: theme.colors.series[index],
				borderColor: theme.colors.surface,
				borderWidth: 1,
				pointRadius: 4,
				pointHoverRadius: 5,
			})),
		},
		options: {
			// A bubble can be wider than the headroom below, so the canvas keeps
			// room for the largest one at the edge.
			layout: { padding: spec.kind === "bubble" ? 22 : 0 },
			// Headroom, so a point or bubble at the end of the range is not cut
			// in half by the edge of the plot.
			scales: {
				x: valueAxis(theme, spec.x, { type: "linear", grace: "5%" }),
				y: valueAxis(theme, spec.y, { grace: "5%" }),
			},
		},
		// The series on a line of its own, then a line per value.
		label: ({ datasetIndex, dataIndex }) => {
			const series = spec.series[datasetIndex];
			return [series.label, ...series.display[dataIndex]];
		},
	};
}

const CONFIGS = {
	line: categoryConfig,
	area: categoryConfig,
	bar: categoryConfig,
	pie: pieConfig,
	doughnut: pieConfig,
	scatter: pointConfig,
	bubble: pointConfig,
};

export function draw(canvas, spec, { animate = true } = {}) {
	const colors = palette(canvas);
	const font = { family: getComputedStyle(canvas).fontFamily, size: 11, weight: 500 };
	const theme = { colors, ticks: { color: colors.axis, font } };
	const { type, data, options, label, swatch } = CONFIGS[spec.kind](spec, theme);

	return new Chart(canvas, {
		type,
		data,
		options: {
			...options,
			animation: animate && !matchMedia("(prefers-reduced-motion: reduce)").matches,
			maintainAspectRatio: false,
			plugins: {
				tooltip: {
					backgroundColor: colors.tooltip,
					titleColor: colors.tooltipText,
					bodyColor: colors.tooltipText,
					titleFont: { family: font.family },
					bodyFont: { family: font.family },
					cornerRadius: 6,
					callbacks: {
						label: (item) => [label(item)].flat().map((line) => ` ${line}`),
						...(swatch && { labelColor: swatch }),
					},
				},
			},
		},
	});
}
