/**
 * The $toast magic: raise a toast from the browser.
 *
 * Toasts normally arrive from the server, merged into the region by id. This
 * is for the things the server never hears about - a copy to the clipboard,
 * going offline - where a round trip would exist only to produce a sentence.
 *
 * The markup is cloned from the templates the region renders, so a toast
 * raised here is the same element as one raised on the server rather than a
 * second copy of the markup living in JavaScript.
 */

const REGION_ID = "hue-toasts";
const VARIANTS = ["success", "danger", "warning", "info", "loading"];

function raise(variant, title, options = {}) {
	const region = document.getElementById(REGION_ID);
	if (!region) {
		console.warn(`[hue] $toast: no ToastRegion on the page, dropped "${title}"`);
		return;
	}

	const template = region.querySelector(`template[data-variant="${variant}"]`);
	const toast = template.content.firstElementChild.cloneNode(true);

	toast.querySelector("[data-toast-title]").textContent = title;
	const description = toast.querySelector("[data-toast-description]");
	if (options.description) {
		description.textContent = options.description;
	} else {
		description.remove();
	}

	// undefined keeps the region's default; null is a toast that stays.
	if (options.duration !== undefined) {
		const ms = options.duration === null ? 0 : options.duration;
		const init = toast.getAttribute("x-init").replace(/start\([^)]*\)/, `start(${ms})`);
		toast.setAttribute("x-init", init);
	}

	region.appendChild(toast);
	return toast;
}

export function registerToastMagic(Alpine) {
	const api = {};
	for (const variant of VARIANTS) {
		api[variant] = (title, options) => raise(variant, title, options);
	}
	Alpine.magic("toast", () => api);
}
