/**
 * hueCalendar: what a declared calendar does in the browser that a link or
 * a form cannot.
 *
 * A click on an empty part of a day, in the time grid, the month or the
 * agenda, opens the event dialog for that day, and the sidebar folds away
 * on a narrow screen. In the time grid the click also posts the half hour
 * under the pointer; everything else a new event starts with is the
 * server's to fill in. The state a click posts is read from the page at
 * the click, since this root is drawn once and the calendar moves under
 * it. Focus across a swap is ajax-focus.js's, for every component.
 *
 * The state is named calendar-something so that no Popover or Dialog
 * inside, whose own state is open, can shadow it.
 *
 * Dragging an event to move or resize it will post to the same save action
 * with the event's id and its new times, and attaches here.
 */
export function registerCalendarData(Alpine) {
	Alpine.data(
		"hueCalendar",
		({ url = null, target = "", state = "", fields = {}, hour = 48 } = {}) => ({
			calendarSide: false,

			calendarCreate() {
				this.calendarOpen(new FormData());
			},

			calendarSlot(event) {
				// Not on an event, a day's number or a popover over either.
				if (event.target.closest("a, button, [role=dialog]")) return;
				const cell = event.target.closest("[data-date]");
				if (!cell) return;
				const body = new FormData();
				body.set(fields.day, cell.dataset.date);
				if ("timed" in cell.dataset) {
					const top = cell.getBoundingClientRect().top;
					const half = Math.floor(((event.clientY - top) / hour) * 2);
					const from = Math.min(Math.max(half * 30, 0), 23 * 60 + 30);
					body.set(fields.time, clock(from));
				}
				this.calendarOpen(body);
			},

			calendarOpen(body) {
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
