/**
 * hueChart: a chart, drawn by a library this bundle does not contain.
 *
 * Chart.js is larger than everything else hue ships put together, and most
 * pages draw no chart, so it lives in chart-bundle.js and is fetched when a
 * chart first appears. Its URL is resolved against this bundle's own, so the
 * two only need to sit side by side however they are served.
 *
 * A chart whose library fails to load says so through failed, for the markup
 * to offer retry() in its place. A drawn chart is drawn again when the theme
 * changes, since the canvas holds colours rather than the tokens they came
 * from.
 */

const CHART_BUNDLE = new URL("./chart-bundle.js", import.meta.url).href;

// One request however many charts the page draws, and the request that
// failed, if the last one did.
let loading = null;
let rejected = null;
// A failed import may stay failed for the life of the page, so another
// attempt asks under a URL the browser has not seen yet.
let attempt = 0;
// Charts the last failure left showing Retry. A retry on any of them draws
// them all, since they were all waiting on the same library.
const stranded = new Set();

function library() {
	const url = attempt ? `${CHART_BUNDLE}?attempt=${attempt}` : CHART_BUNDLE;
	loading ??= import(url).catch((error) => {
		// Logged here rather than per chart: one request failed, however
		// many charts were waiting on it.
		console.error(
			`hue could not load ${url}, which charts are drawn with. ` +
				"Serve it from the same directory as hue's main bundle.",
			error,
		);
		rejected = loading;
		throw error;
	});
	return loading;
}

export function registerChartData(Alpine) {
	Alpine.data("hueChart", (spec) => {
		// Kept out of the component's state, which would wrap the chart in a
		// proxy. gone records a removal that happens before the library
		// arrives.
		let chart = null;
		let gone = false;
		let theme = null;

		return {
			failed: false,

			async init() {
				let draw;
				try {
					({ draw } = await library());
					// The font is measured when the chart is laid out and kept
					// until it is drawn again.
					await document.fonts.ready;
				} catch {
					this.failed = true;
					stranded.add(this);
					// Focus sits on the figure only after a retry, so this was
					// that retry failing: hand focus back to the button.
					if (document.activeElement === this.$root) {
						this.$nextTick(() => this.$refs.retry.focus());
					}
					return;
				}
				if (gone || !this.render(draw)) return;
				// Only <html> is watched, which is where the theme store sets
				// data-theme.
				// Only a theme that actually changed is redrawn: the store also
				// writes the value already there when it starts.
				theme = new MutationObserver((records) => {
					const now = document.documentElement.dataset.theme;
					if (records.every((record) => record.oldValue === now)) return;
					chart?.destroy();
					this.render(draw, { animate: false });
				});
				theme.observe(document.documentElement, {
					attributeFilter: ["data-theme"],
					attributeOldValue: true,
				});
			},

			// Caught here because Alpine leaves a rejected init unhandled, which
			// would report a spec the library refuses without its chart.
			render(draw, options) {
				try {
					chart = draw(this.$refs.canvas, spec, options);
					return true;
				} catch (error) {
					chart = null;
					console.error("hue could not draw this chart.", this.$el, error);
					return false;
				}
			},

			retry() {
				// A second press before the first lands would draw twice.
				if (!this.failed) return;
				// The button is about to hide, which would drop focus to the page.
				if (this.$root.contains(document.activeElement)) this.$root.focus();
				// A failure gets one new attempt; one still on its way is
				// waited on instead.
				if (loading === rejected) {
					loading = null;
					attempt += 1;
				}
				const charts = [...stranded];
				stranded.clear();
				return Promise.all(
					charts.map((chart) => {
						chart.failed = false;
						return chart.init();
					}),
				);
			},

			// Escape dismisses the hover tooltip, which can cover the points
			// beside it. Heard on the window in the capture phase, as hue's
			// Tooltip is: the pointer, not focus, put it there, and a showing
			// tooltip takes the first Escape before a dialog or a table around
			// it hears the key. A control whose own popup is open keeps it.
			hideTooltip(event) {
				if (!chart?.tooltip.getActiveElements().length) return;
				if (event.target.getAttribute?.("aria-expanded") === "true") return;
				event.stopPropagation();
				chart.tooltip.setActiveElements([], { x: 0, y: 0 });
				chart.setActiveElements([]);
				chart.update();
			},

			destroy() {
				gone = true;
				stranded.delete(this);
				theme?.disconnect();
				chart?.destroy();
			},
		};
	});
}
