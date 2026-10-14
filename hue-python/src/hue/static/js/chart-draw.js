/**
 * Entry point for chart-bundle.js, which chart-loader.js fetches. It registers
 * only what a line, area or bar chart needs, so the rest of Chart.js stays out.
 *
 * draw() takes the spec the Chart component renders and turns it into a
 * Chart.js config, with every colour read from the design tokens at the time
 * it is called. A canvas cannot follow a CSS variable on its own, so the
 * loader calls draw() again when the theme changes.
 */
import {
	BarController,
	BarElement,
	CategoryScale,
	Chart,
	Filler,
	LinearScale,
	LineController,
	LineElement,
	PointElement,
	Tooltip,
} from "chart.js";

Chart.register(
	BarController,
	BarElement,
	CategoryScale,
	Filler,
	LinearScale,
	LineController,
	LineElement,
	PointElement,
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

// The Chart component's legend names the same tokens for its swatches.
function palette(canvas) {
	const vivid = (percent) =>
		`color-mix(in srgb, var(--color-accent-vivid) ${percent}%, transparent)`;
	return resolve(canvas, {
		accent: "var(--color-accent)",
		muted: "var(--color-fg-subtle)",
		grid: "var(--color-border)",
		surface: "var(--color-surface)",
		tooltip: "var(--color-fg-strong)",
		tooltipText: "var(--color-canvas)",
		areaTop: vivid(24),
		areaBottom: vivid(0),
	});
}

function axisFormat(spec) {
	// English and the currency's code, like the values the component writes
	// for the tooltip and the table, so the axis does not group digits or mark
	// money differently from them.
	return new Intl.NumberFormat("en", {
		notation: "compact",
		currencyDisplay: "code",
		style: spec.format === "number" ? "decimal" : spec.format,
		currency: spec.format === "currency" ? spec.currency : undefined,
	});
}

function dataset(spec, series, index, colors) {
	const main = index === 0;

	if (spec.kind === "bar") {
		return {
			label: series.label,
			data: series.values,
			backgroundColor: main
				? series.values.map((_, i) =>
						spec.highlight === null || spec.highlight === i ? colors.accent : colors.muted,
					)
				: colors.muted,
			borderRadius: 3,
			maxBarThickness: 44,
		};
	}

	const color = main ? colors.accent : colors.muted;
	const last = series.values.length - 1;
	return {
		label: series.label,
		data: series.values,
		borderColor: color,
		borderWidth: main ? 2 : 1.5,
		borderDash: main ? [] : [4, 4],
		// Only the latest point is marked, which is also what keeps a series of
		// one value from drawing nothing at all.
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
}

export function draw(canvas, spec, { animate = true } = {}) {
	const colors = palette(canvas);
	const font = getComputedStyle(canvas).fontFamily;
	const ticks = { color: colors.muted, font: { family: font, size: 11, weight: 500 } };
	const format = axisFormat(spec);

	return new Chart(canvas, {
		type: spec.kind === "bar" ? "bar" : "line",
		data: {
			labels: spec.labels,
			// Chart.js paints the first dataset last, so the main series sits on
			// top of its comparison.
			datasets: spec.series.map((series, index) => dataset(spec, series, index, colors)),
		},
		options: {
			animation: animate && !matchMedia("(prefers-reduced-motion: reduce)").matches,
			maintainAspectRatio: false,
			interaction: { mode: "index", intersect: false },
			scales: {
				x: { grid: { display: false }, border: { display: false }, ticks: { ...ticks, maxRotation: 0, autoSkipPadding: 16 } },
				y: {
					beginAtZero: true,
					grid: { color: colors.grid },
					border: { display: false },
					ticks: { ...ticks, maxTicksLimit: 5, callback: (value) => format.format(value) },
				},
			},
			plugins: {
				tooltip: {
					backgroundColor: colors.tooltip,
					titleColor: colors.tooltipText,
					bodyColor: colors.tooltipText,
					titleFont: { family: font },
					bodyFont: { family: font },
					cornerRadius: 6,
					callbacks: {
						label: ({ datasetIndex, dataIndex }) => {
							const series = spec.series[datasetIndex];
							return ` ${series.label}: ${series.display[dataIndex]}`;
						},
					},
				},
			},
		},
	});
}
