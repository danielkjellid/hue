/**
 * Clear the aria-busy marks Alpine AJAX leaves behind.
 *
 * Alpine AJAX marks every element a request targets, every x-sync element
 * included, and clears a mark when it merges that element. Two marks are never
 * cleared (as of 0.12.7): a synced element the response did not contain, and
 * every target of a request that failed before any response arrived. A table's
 * rows stay dimmed after either.
 *
 * So hue clears the marks it saw a request place, once no request is in flight.
 * Waiting for all of them rather than one keeps a mark that a later request
 * still owns, which a per-request answer cannot tell apart when two requests
 * come from the same element. Delete this when the fix lands upstream.
 */

const marked = new Set();
let inFlight = 0;

function finished() {
	inFlight = Math.max(0, inFlight - 1);
	if (inFlight > 0) return;
	// After the response is merged, which Alpine AJAX does once ajax:sent has
	// fired, including any status target such as x-target.422 that plans the
	// request again.
	setTimeout(() => {
		if (inFlight > 0) return;
		for (const el of marked) el.removeAttribute("aria-busy");
		marked.clear();
	});
}

// A failed fetch fires no Alpine AJAX event. It surfaces as an uncaught
// TypeError instead: a rejected promise from a form or a link, an error that
// Alpine rethrows from a $ajax expression. Another TypeError while a request
// is in flight only clears its marks early.
function failed(error) {
	if (inFlight > 0 && error instanceof TypeError) finished();
}

export function clearStaleBusyMarks() {
	document.addEventListener("ajax:send", (event) => {
		inFlight++;
		const planned = event.detail?.headers?.["X-Alpine-Target"] ?? "";
		for (const id of planned.split(" ").filter(Boolean)) {
			const el = document.getElementById(id);
			if (el) marked.add(el);
		}
	});
	document.addEventListener("ajax:sent", finished);
	window.addEventListener("unhandledrejection", (event) =>
		failed(event.reason),
	);
	window.addEventListener("error", (event) => failed(event.error));
}
