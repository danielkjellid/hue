import anchor from "@alpinejs/anchor";
import focus from "@alpinejs/focus";
import ajax from "@imacrayon/alpine-ajax";
import Alpine from "alpinejs";
import { registerScrollAreaData } from "./scroll-area.js";
import { registerTableData } from "./table.js";
import { registerThemeStore } from "./theme.js";
import { registerToastMagic } from "./toast.js";

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

	registerScrollAreaData(Alpine);
	registerTableData(Alpine);
	registerThemeStore(Alpine, themeStorageKey);
	registerToastMagic(Alpine);

	Alpine.start();

	return Alpine;
}

// Also export Alpine and ajax for direct access if needed
export { Alpine, ajax };
