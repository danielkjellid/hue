/**
 * What a swap needs from hue besides Alpine AJAX: focus that survives it.
 */

/**
 * Put focus back after a swap replaces the element that had it.
 *
 * Alpine AJAX only moves focus to an autofocus element in what it merged
 * (as of 0.12.7). A link or button that a swap replaces takes focus down
 * to the body with it, and the next Enter does nothing. So hue notes what
 * had focus when a request starts, and once the response is merged it
 * focuses the element with the same id in the new markup. When that one
 * is gone or hidden, such as a Reset that has nothing left to reset, it
 * tries the ids in the element's data-hue-refocus, in order.
 *
 * It only acts when focus is on the body and the element it noted is gone
 * or hidden, so it never pulls focus from wherever the reader moved it
 * while the request was in flight.
 */
export function keepFocusThroughSwaps() {
	let kept = null;

	document.addEventListener("ajax:before", () => {
		const focused = document.activeElement;
		kept = focused && focused !== document.body ? focused : null;
	});

	// On window, because Alpine AJAX fires ajax:after there when the element
	// that sent the request was swapped away.
	window.addEventListener("ajax:after", () => {
		const lost = kept;
		kept = null;
		if (!lost) return;
		// After Alpine AJAX's own autofocus, which also waits a task.
		setTimeout(() => {
			const active = document.activeElement;
			if (active && active !== document.body) return;
			if (lost.isConnected && lost.getClientRects().length) return;
			const ids = [lost.id, ...(lost.dataset.hueRefocus ?? "").split(" ")];
			for (const id of ids.filter(Boolean)) {
				const found = document.getElementById(id);
				found?.focus();
				if (found && document.activeElement === found) return;
			}
		});
	});
}
