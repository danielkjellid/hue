/**
 * hueDismissible: a box with a close button inside it.
 *
 * Hiding the box takes the focused close button with it, and the browser
 * drops focus to the body, which sends a keyboard or screen reader user back
 * to the top of the page. So focus moves first, to whatever the reader would
 * have tabbed to next, or to the one before when the box was the last thing
 * on the page.
 */

function landing(focus, root) {
	const reachable = focus
		.within(document.body)
		.all()
		.filter(
			(el) =>
				!root.contains(el) && el.tabIndex >= 0 && el.getClientRects().length > 0,
		);
	const after = reachable.find(
		(el) => root.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING,
	);
	if (after) return after;
	const before = reachable.findLast(
		(el) => root.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING,
	);
	if (before) return before;

	// Nothing else on the page takes focus. The box's container stays where
	// the box was, so focus waits there rather than at the top of the page.
	const parent = root.parentElement ?? document.body;
	if (!parent.hasAttribute("tabindex")) parent.setAttribute("tabindex", "-1");
	return parent;
}

export function registerDismissibleData(Alpine) {
	Alpine.data("hueDismissible", () => ({
		shown: true,

		dismiss() {
			// Focus that is somewhere else already is left where it is.
			if (this.$root.contains(document.activeElement)) {
				landing(this.$focus, this.$root).focus();
			}
			this.shown = false;
		},
	}));
}
