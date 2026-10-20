/**
 * Put focus back after an Alpine AJAX swap.
 *
 * Alpine AJAX replaces the children of every target and puts focus nowhere,
 * so a link or a box that had focus inside one drops focus to the body and
 * the next Tab starts from the top of the page. Only [x-autofocus] in the
 * new content is focused (0.12.7, render()), and the server cannot know
 * which control was pressed.
 *
 * So the focused element's id, and the ids of its ancestors, are noted as a
 * request goes out, and once the response is in and focus has been lost,
 * the first of them still on the page gets it back: the control itself when
 * it was drawn again, else the nearest named ancestor, which hands it to its
 * roving tab stop or its current item when it has one and is made focusable
 * for the purpose when not. A control without an id, inside nothing with
 * one, gets nothing.
 *
 * An ancestor says where focus goes instead when what had it is gone with
 * data-hue-refocus="<id>". A dialog's slot names the button that opens the
 * dialog, since the control that closed the dialog went with it.
 */

let noted = null;

export function restoreFocusAfterSwap() {
	document.addEventListener("ajax:before", remember);
	// On the window: ajax:after goes to the window itself when the control
	// that made the request is gone by the time the response is in, and an
	// event on a detached element reaches nothing else.
	window.addEventListener("ajax:after", restore);
}

function remember() {
	const el = document.activeElement;
	if (!el || el === document.body) {
		noted = null;
		return;
	}
	const chain = [];
	for (let node = el; node && node !== document.body; node = node.parentElement) {
		if (node.id) chain.push(node.id);
	}
	noted = { id: el.id, chain };
}

function restore() {
	const was = noted;
	noted = null;
	if (!was || document.activeElement !== document.body) return;
	// After Alpine has bound the new elements, so a roving tab stop is
	// there to be found.
	setTimeout(() => {
		if (document.activeElement !== document.body) return;
		for (const id of was.chain) {
			const el = document.getElementById(id);
			if (!el) continue;
			const to = id === was.id ? el : landing(el);
			if (to.tabIndex < 0 && !to.hasAttribute("tabindex")) {
				to.setAttribute("tabindex", "-1");
			}
			to.focus({ preventScroll: true });
			return;
		}
	});
}

function landing(ancestor) {
	const named = ancestor.dataset.hueRefocus;
	return (
		(named && document.getElementById(named)) ||
		ancestor.querySelector('[tabindex="0"], [aria-current]') ||
		ancestor
	);
}
