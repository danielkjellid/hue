/**
 * What a swap needs from hue besides Alpine AJAX: focus that survives it, a
 * first history entry that Back can return to, and the title of the page it
 * lands on.
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
 * When none of those is left either, the nearest ancestor with an id that
 * is still on the page takes focus: the id in its own data-hue-refocus,
 * else its roving tab stop or current item, else the ancestor itself. A
 * calendar's dialog slot names New event that way, since the control that
 * closed the dialog went with it.
 *
 * It only acts when focus is on the body and the element it noted is gone
 * or hidden, so it never pulls focus from wherever the reader moved it
 * while the request was in flight.
 */
export function keepFocusThroughSwaps() {
	let kept = null;
	let around = [];

	document.addEventListener("ajax:before", () => {
		const focused = document.activeElement;
		kept = focused && focused !== document.body ? focused : null;
		around = [];
		for (
			let node = kept?.parentElement;
			node && node !== document.body;
			node = node.parentElement
		) {
			if (node.id) around.push(node.id);
		}
	});

	// On window, because Alpine AJAX fires ajax:after there when the element
	// that sent the request was swapped away.
	window.addEventListener("ajax:after", () => {
		const lost = kept;
		const ancestors = around;
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
			const ancestor = ancestors
				.map((id) => document.getElementById(id))
				.find(Boolean);
			if (ancestor) landing(ancestor).focus({ preventScroll: true });
		});
	});
}

function landing(ancestor) {
	const named = ancestor.dataset.hueRefocus;
	const to =
		(named && document.getElementById(named)) ||
		ancestor.querySelector('[tabindex="0"], [aria-current]') ||
		ancestor;
	if (to.tabIndex < 0 && !to.hasAttribute("tabindex"))
		to.setAttribute("tabindex", "-1");
	return to;
}

/**
 * Keep the history a swap makes true to the pages in it.
 *
 * Let Back return to the page as it was before the first swap.
 *
 * Alpine AJAX reloads the page on Back only when the entry it lands on was
 * one of its own, marked __ajax. The entry the page loaded in is not, so
 * Back to it would change the address and leave the swapped region alone.
 * hue marks that entry too, just before the first swap pushes, so Back
 * reloads it like any other. A page that never pushes keeps
 * plain history, so Back from a #fragment link is not a reload there.
 */
export function markFirstHistoryEntry() {
	document.addEventListener("ajax:before", (event) => {
		if (history.state?.__ajax) return;
		if (!event.target.hasAttribute?.("x-target.push")) return;
		history.replaceState({ ...history.state, __ajax: true }, "");
	});

	// Alpine AJAX merges the targets and leaves the head alone, so a swap
	// that moved the address kept the old page's title, in the tab and on
	// the history entry it made. Once the address is the response's own,
	// the entry is that page, and so is its title.
	window.addEventListener("ajax:after", (event) => {
		const response = event.detail?.response;
		const title = response?.html?.querySelector("title");
		if (title && response.url === location.href) {
			document.title = title.textContent;
		}
	});
}
