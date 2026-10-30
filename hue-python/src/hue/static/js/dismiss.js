/**
 * Moving focus off something that is about to disappear.
 *
 * Hiding or removing the element that has focus drops focus to the body,
 * which sends a keyboard or screen reader user back to the top of the page.
 * So whatever dismisses itself (an Alert, a Toast) hands focus on first, all
 * through the one $handOff, so they agree on where it goes.
 */

/**
 * Focus the place the reader would have tabbed to next.
 *
 * Looked for inside `within`: the next focusable element after `root`, else
 * the one before it. Failing that `returnTo`, where focus was before it came
 * in, if it is still on the page. Failing that `fallback`, made focusable for
 * the purpose, which stays where `root` was.
 *
 * Both default to the dialog around `root`, if there is one: a modal's focus
 * trap refuses anything outside it, which would leave focus on the element
 * that is hiding.
 *
 * Anything inert is passed over, so an element on its way out is not chosen.
 */
const DIALOG = "[role=dialog], [role=alertdialog]";

function handOff(
	focus,
	root,
	{
		within = root.parentElement?.closest(DIALOG) ?? document.body,
		returnTo = null,
		fallback = root.parentElement?.closest(DIALOG) ??
			root.parentElement ??
			document.body,
	} = {},
) {
	const reachable = focus
		.within(within)
		.all()
		.filter(
			(el) =>
				!root.contains(el) &&
				!el.closest("[inert]") &&
				el.tabIndex >= 0 &&
				el.getClientRects().length > 0,
		);
	const after = reachable.find(
		(el) => root.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING,
	);
	const before = reachable.findLast(
		(el) => root.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING,
	);
	const landing = after ?? before ?? (returnTo?.isConnected ? returnTo : null);
	if (landing) return landing.focus();

	if (!fallback.hasAttribute("tabindex"))
		fallback.setAttribute("tabindex", "-1");
	fallback.focus();
}

export function registerDismissibleData(Alpine) {
	// $handOff(root, options): for an inline expression, such as an Alert's
	// or a Toast's, which cannot import this module.
	Alpine.magic(
		"handOff",
		(el) => (root, options) =>
			handOff(Alpine.evaluate(el, "$focus"), root, options),
	);
}
