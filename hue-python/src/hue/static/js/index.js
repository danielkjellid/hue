import ajax from "@imacrayon/alpine-ajax";
import Alpine from "alpinejs";
import { registerThemeStore } from "./theme.js";

// Make Alpine available globally
window.Alpine = Alpine;

// Register the ajax plugin
Alpine.plugin(ajax);

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

	registerThemeStore(Alpine, themeStorageKey);

	Alpine.start();

	return Alpine;
}

// Also export Alpine and ajax for direct access if needed
export { Alpine, ajax };
