/**
 * hueCalendar: what a declared calendar does in the browser that a link or
 * a form cannot.
 *
 * A click on an empty part of a day, in the time grid, the month or the
 * agenda, opens the event dialog with that time filled in, and the sidebar
 * folds away on a narrow screen. The state a click posts is read from the
 * page at the click, since this root is drawn once and the calendar moves
 * under it.
 *
 * It also keeps focus across a swap. Alpine AJAX replaces what a link or a
 * form points at and puts focus nowhere, so Previous, a day in the picker
 * or a calendar's box would drop focus to the body on every press. The
 * focused element's id, and its ancestors' ids, are noted as the request
 * goes out and the first that still exists is focused once it is back.
 *
 * Dragging an event to move or resize it will post to the same save action
 * with the event's id and its new times, and attaches here.
 */
export function registerCalendarData(Alpine) {
	Alpine.data(
		"hueCalendar",
		({ url = null, target = "", state = "", home = "", hour = 48 } = {}) => ({
			side: false,
			focused: null,

			init() {
				this.$root.addEventListener("ajax:before", () => this.remember());
				this.restore = () => this.refocus();
				// On the window: the element that made the request is often
				// gone by the time the response is in, and an event on a
				// detached element reaches nothing else.
				window.addEventListener("ajax:after", this.restore);
			},

			destroy() {
				window.removeEventListener("ajax:after", this.restore);
			},

			remember() {
				const el = document.activeElement;
				if (!this.$root.contains(el)) return;
				const chain = [];
				for (let node = el; node && node !== this.$root; node = node.parentElement) {
					if (node.id) chain.push(node.id);
				}
				this.focused = { id: el.id, chain, inDialog: chain.includes(target) };
			},

			refocus() {
				const noted = this.focused;
				this.focused = null;
				if (!noted || document.activeElement !== document.body) return;
				// After Alpine has bound the new elements, so the picker's
				// roving tab stop is there to be found.
				setTimeout(() => {
					if (document.activeElement !== document.body) return;
					// The dialog has closed and what opened it may be gone
					// with the sidebar's refresh: New event is the one
					// control that is always there to land on.
					const ids = noted.inDialog ? [home, ...noted.chain] : noted.chain;
					for (const id of ids) {
						const el = document.getElementById(id);
						if (!el || id === target) continue;
						const to =
							id === noted.id
								? el
								: el.querySelector('[tabindex="0"], [aria-current]') || el;
						if (to.tabIndex < 0 && !to.hasAttribute("tabindex")) {
							to.setAttribute("tabindex", "-1");
						}
						to.focus({ preventScroll: true });
						return;
					}
				});
			},

			create() {
				this.open(new FormData());
			},

			slot(event) {
				// Not on an event, a day's number or a popover over either.
				if (event.target.closest("a, button, [role=dialog]")) return;
				const cell = event.target.closest("[data-date]");
				if (!cell) return;
				const day = cell.dataset.date;
				// The half hour under the pointer in the time grid, whose
				// columns are divs; a month cell or an agenda day starts at nine.
				let from = 9 * 60;
				if (cell.tagName === "DIV") {
					const top = cell.getBoundingClientRect().top;
					const half = Math.floor(((event.clientY - top) / hour) * 2);
					from = Math.min(Math.max(half * 30, 0), 23 * 60);
				}
				const body = new FormData();
				body.set("starts", day);
				body.set("starts_time", clock(from));
				body.set("ends", day);
				body.set("ends_time", clock(Math.min(from + 60, 23 * 60 + 59)));
				this.open(body);
			},

			open(body) {
				if (!url) return;
				const carried = document.getElementById(state);
				for (const input of carried?.querySelectorAll("input") ?? []) {
					body.append(input.name, input.value);
				}
				this.$ajax(url, { method: "post", target, body });
			},
		}),
	);
}

function clock(minutes) {
	const hours = String(Math.floor(minutes / 60)).padStart(2, "0");
	return `${hours}:${String(minutes % 60).padStart(2, "0")}`;
}
