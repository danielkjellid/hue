/**
 * Put focus back on the control that started a request.
 *
 * Alpine AJAX's update merge replaces the children of a target, and a link
 * inside it that had focus goes with them: focus drops to <body>, and the
 * next Tab starts from the top of the page. Only [x-autofocus] in the new
 * content is focused afterwards (0.12.7, render()), and the server cannot
 * know which link was pressed. So the control's id is remembered before the
 * request and, once the response is merged, an element with that id is
 * focused again if focus was lost. A control without an id gets nothing.
 */

let focusedId = null;

export function restoreFocusAfterSwap() {
	// Both events bubble: ajax:before from the control, ajax:merged from
	// each target.
	document.addEventListener("ajax:before", () => {
		focusedId = document.activeElement?.id || null;
	});
	document.addEventListener("ajax:merged", () => {
		if (!focusedId || document.activeElement !== document.body) return;
		document.getElementById(focusedId)?.focus();
	});
}
