/**
 * Entry point for chart-bundle.js, which chart-loader.js fetches. It registers
 * only what a line, area or bar chart needs, so the rest of Chart.js stays out.
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

export function draw(canvas, config) {
	return new Chart(canvas, config);
}
