import anchor from "@alpinejs/anchor";
import focus from "@alpinejs/focus";
import ajax from "@imacrayon/alpine-ajax";
import Alpine from "alpinejs";
import { registerComboboxData } from "./combobox.js";
import { registerCommandData } from "./command.js";
import { registerDismissibleData } from "./dismiss.js";
import { registerScrollAreaData } from "./scroll-area.js";
import { registerSelectData } from "./select.js";
import {
	registerTableColumns,
	registerTableSelection,
	registerTableFilters,
	registerTableReset,
	registerTableSearch,
} from "./table.js";
import { registerThemeStore } from "./theme.js";
import { registerToastMagic } from "./toast.js";
import { registerTocData } from "./toc.js";

// Make Alpine available globally
window.Alpine = Alpine;

Alpine.plugin(ajax);
// x-trap for modal overlays (dialog, drawer, command palette): it traps focus,
// restores it to the trigger on close, and adds inert/noscroll for the rest of
// the page. x-anchor positions the non-modal panels (popover, menu, listbox,
// tooltip) and keeps them inside the viewport.
Alpine.plugin(focus);
Alpine.plugin(anchor);

/**
 * Wire up the page-level Alpine configuration and start Alpine.
 *
 * Called once from the inline bootstrap script BasePage renders, which is where
 * the server-side values (CSRF token, theme storage key) come from.
 */
export function configureAlpine({ csrfToken, themeStorageKey }) {
	ajax.configure({
		mergeStrategy: "update",
		headers: {
			"X-CSRFToken": csrfToken,
		},
	});

	// A request that syncs marks every x-sync element busy, the toast region
	// and a table's rows among them, and Alpine AJAX clears the mark only on
	// those the response brought back. These listeners clear the rest. The
	// response is read at ajax:sent, before a merge can move its elements out,
	// and the marks are cleared a microtask later, after a status target such
	// as x-target.422 has planned the request again and re-marked them.
	//
	// Only a request's own marks are cleared, since a later request that marked
	// the same element owns it. Requests are told apart by the element that
	// sent them, so a second request from the same element can have its marks
	// cleared early by the first answer. That is cosmetic: Alpine AJAX cannot
	// tell the two answers apart, while tracking requests in a queue here could
	// leave a mark for good once one failed without answering.
	document.addEventListener("ajax:send", (event) => {
		const request = {};
		event.target._hueRequest = request;
		const planned = event.detail?.headers?.["X-Alpine-Target"] ?? "";
		for (const id of planned.split(" ").filter(Boolean)) {
			const synced = document.getElementById(id);
			if (synced?.hasAttribute("x-sync")) synced._hueBusyFor = request;
		}
	});
	document.addEventListener("ajax:sent", (event) => {
		const html = event.detail?.html;
		const request = event.target._hueRequest;
		if (!request || typeof html?.getElementById !== "function") return;
		const absent = [...document.querySelectorAll("[x-sync]")].filter(
			(el) => el._hueBusyFor === request && !html.getElementById(el.id),
		);
		queueMicrotask(() => {
			for (const el of absent) el.removeAttribute("aria-busy");
		});
	});

	registerComboboxData(Alpine);
	registerCommandData(Alpine);
	registerDismissibleData(Alpine);
	registerScrollAreaData(Alpine);
	registerSelectData(Alpine);
	registerTableSelection(Alpine);
	registerTableSearch(Alpine);
	registerTableFilters(Alpine);
	registerTableColumns(Alpine);
	registerTableReset(Alpine);
	registerThemeStore(Alpine, themeStorageKey);
	registerToastMagic(Alpine);
	registerTocData(Alpine);

	Alpine.start();

	return Alpine;
}

// Also export Alpine and ajax for direct access if needed
export { Alpine, ajax };
