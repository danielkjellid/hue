/**
 * hueCalendar: what a declared calendar does in the browser that a link or
 * a form cannot.
 *
 * A click on an empty part of a day, in the time grid, the month or the
 * agenda, opens the event dialog for that day, and the sidebar folds away
 * on a narrow screen. In the time grid the click also posts the half hour
 * under the pointer; everything else a new event starts with is the
 * server's to fill in.
 *
 * With a move URL the events can be dragged, by one pointer drag for every
 * view. In the time grid a press on an empty slot draws a ghost and opens
 * the dialog over the dragged range, a press on an event moves it, up and
 * down and across the day columns, and one on its bottom edge changes when
 * it ends, all snapped to the quarter hour. A chip in the month and a bar
 * in the all-day row move by whole days, counted from the day they were
 * taken hold of by. Alt with an arrow key moves the focused event the same
 * way without a pointer, and with Shift changes its end.
 *
 * The browser owns nothing: a change posts the id, the occurrence and the
 * new times to the route, which looks the event up and redraws. A press
 * that never travels five pixels is a click, and a drag that ends where it
 * began, or is cancelled, by Escape or by a redraw under it, puts the event
 * back. The state a request posts is read from the page at the time, since
 * this root is drawn once and the calendar moves under it. Focus across a
 * swap is ajax-focus.js's, for every component. After a move or an Undo the
 * answer marks where focus goes with x-autofocus, which Alpine AJAX takes
 * before ajax-focus.js looks.
 *
 * The state is named calendar-something so that no Popover or Dialog
 * inside, whose own state is open, can shadow it.
 */

// Minutes a drag snaps to, and pixels a press travels before it is one.
const SNAP = 15;
const THRESHOLD = 5;
const DAY = 24 * 60;
// Tailwind's md, under which a month cell shows bars and the week is a day.
const NARROW = "(max-width: 767px)";

// Alt with an arrow key: the days and the minutes it moves the event by.
const STEPS = {
	ArrowUp: [0, -SNAP],
	ArrowDown: [0, SNAP],
	ArrowLeft: [-1, 0],
	ArrowRight: [1, 0],
};

const GHOST =
	"pointer-events-none absolute inset-x-0.5 z-10 rounded-sm border border-dashed " +
	"border-accent bg-accent-subtle px-1.5 py-0.5 text-xs font-semibold tabular-nums text-accent-text";
const DRAGGING = ["z-20", "opacity-90", "shadow-overlay"];
const DROP = ["ring-2", "ring-inset", "ring-accent"];

export function registerCalendarData(Alpine) {
	Alpine.data(
		"hueCalendar",
		({
			url = null,
			move = null,
			key = "",
			target = "",
			state = "",
			fields = {},
			hour = 48,
		} = {}) => ({
			calendarSide: false,
			// Where the time grid was scrolled to before the last swap, which
			// the grid drawn by the response starts from.
			gridScroll: null,
			// The press or drag in progress, or null.
			drag: null,
			// Set as a drag ends, so the click the browser sends after it
			// opens neither the popover nor the dialog.
			swallow: false,
			// Set while a move is posted, so a held key does not post the
			// time the event had before it moved again.
			moving: false,

			init() {
				const calendar = document.getElementById(key);
				if (!calendar) return;
				this.$root.addEventListener("ajax:before", () => {
					this.gridScroll =
						calendar.querySelector("[data-time-grid]")?.scrollTop ?? null;
				});
				const narrow = matchMedia(NARROW);
				const fit = () => this.fit(narrow.matches);
				// After the tick, so the grid has scrolled to where it opens
				// before the swap notes where it was.
				this.$nextTick(fit);
				narrow.addEventListener("change", fit);
				if (!move) return;
				calendar.addEventListener(
					"click",
					(event) => {
						if (!this.swallow) return;
						event.stopPropagation();
						event.preventDefault();
					},
					true,
				);
				const handlers = {
					pointerdown: "press",
					pointermove: "stretch",
					pointerup: "release",
					pointercancel: "cancel",
					// After pointerup as well, by when there is no drag left.
					lostpointercapture: "cancel",
					keydown: "keys",
				};
				for (const [type, name] of Object.entries(handlers)) {
					calendar.addEventListener(type, (event) => this[name](event));
				}
			},

			// A week on a phone is shown as the day it is around: the week
			// tab is current, so the day tab's own link is fetched in its
			// place, without a history entry, and the URL keeps saying week.
			fit(narrow) {
				const week = document.getElementById(`${key}-switch-week`);
				const day = document.getElementById(`${key}-switch-day`);
				if (!narrow || !day || week?.getAttribute("aria-current") !== "page") return;
				this.$ajax(day.href, { target: `${key}-view`, sync: true });
			},

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
				if (url) return this.send(url, body);
			},

			send(action, body) {
				// Under the key, as the dialog posts them.
				const carried = document.getElementById(state);
				for (const input of carried?.querySelectorAll("input") ?? []) {
					body.append(input.name, input.value);
				}
				// sync, or the toast the route raises, which arrives in the
				// synced region, is dropped on the floor.
				return this.$ajax(action, { method: "post", target, body, sync: true });
			},

			minuteAt(column, y) {
				const top = column.getBoundingClientRect().top;
				const minutes = ((y - top) / hour) * 60;
				return Math.min(Math.max(Math.round(minutes / SNAP) * SNAP, 0), DAY);
			},

			columnAt(x) {
				return [...document.querySelectorAll(`#${CSS.escape(key)} div[data-date]`)].find(
					(column) => {
						const box = column.getBoundingClientRect();
						return x >= box.left && x < box.right;
					},
				);
			},

			press(event) {
				if (event.button !== 0) return;
				// One that was cancelled, or redrawn under it, is over.
				if (this.drag?.cancelled || (this.drag && !live(this.drag))) this.cancel();
				if (this.drag) return;
				// A month cell, or along the all-day row the day column under
				// the pointer, is the day an event is taken hold of by: for a
				// bar over several days, not the day it starts. Those move by
				// whole days.
				const cell = event.target.closest("td[data-date]");
				const row = event.target.closest("[data-all-day-row]");
				const column = cell ?? (row ? this.columnAt(event.clientX) : event.target.closest("div[data-date]"));
				if (!column) return;
				const button = event.target.closest("[data-event-id]");
				const at = { x: event.clientX, y: event.clientY, moved: false, column };
				if (button) {
					const li = button.closest("li");
					const mode = event.target.closest("[data-resize]") ? "resize" : "move";
					this.drag = {
						...at,
						mode: cell || row ? "days" : mode,
						button,
						li,
						css: li.style.cssText,
						// Where this part of the event sits in its own column,
						// which for the second day of an overnight event is not
						// where the event starts.
						top: li.offsetTop,
						time: button.querySelector("[data-time]")?.textContent,
						days: 0,
						minutes: 0,
						shift: 0,
					};
					button.setPointerCapture(event.pointerId);
					this.listen();
					return;
				}
				if (cell || row || event.target.closest("a, button, [role=dialog]")) return;
				const from = this.minuteAt(column, event.clientY);
				this.drag = { ...at, mode: "create", from, to: from, ghost: null };
				column.setPointerCapture(event.pointerId);
				this.listen();
			},

			// Escape cancels a drag wherever focus is, which after a press
			// on an empty slot is nowhere in the calendar. On the document
			// for as long as the drag lasts, and first, so nothing else
			// that listens for Escape hears it.
			listen() {
				const escape = (event) => {
					if (event.key !== "Escape") return;
					event.stopPropagation();
					event.preventDefault();
					this.cancel({ keep: true });
				};
				document.addEventListener("keydown", escape, true);
				this.drag.unlisten = () => document.removeEventListener("keydown", escape, true);
			},

			stretch(event) {
				const drag = this.drag;
				if (!drag || drag.cancelled) return;
				if (!live(drag)) return this.cancel();
				if (!drag.moved) {
					if (Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < THRESHOLD) return;
					drag.moved = true;
					drag.column.parentElement.classList.add("select-none");
					if (drag.mode === "create") {
						drag.ghost = Object.assign(document.createElement("div"), { className: GHOST });
						drag.column.appendChild(drag.ghost);
					} else {
						drag.li.classList.add(...DRAGGING);
					}
				}
				if (drag.mode === "create") {
					drag.to = this.minuteAt(drag.column, event.clientY);
					const [a, b] = span(drag.from, drag.to);
					drag.ghost.style.top = `${(a * hour) / 60}px`;
					drag.ghost.style.height = `${((b - a) * hour) / 60 - 2}px`;
					drag.ghost.textContent = `${clock(a)} – ${clock(b)}`;
					return;
				}
				if (drag.mode === "days") return this.shiftDays(drag, event);
				const at = when(drag.button);
				const [low, high] = bounds(at, drag.mode);
				const minutes = Math.round(((event.clientY - drag.y) / hour) * 60 / SNAP) * SNAP;
				drag.minutes = Math.min(Math.max(minutes, low), high);
				if (drag.mode === "resize") {
					drag.li.style.height = `${((at.length + drag.minutes) * hour) / 60 - 2}px`;
					readout(drag.button, at.starts, at.ends + drag.minutes);
					return;
				}
				const column = this.columnAt(event.clientX);
				if (column) {
					drag.days = daysBetween(drag.column.dataset.date, column.dataset.date);
					drag.shift = left(column) - left(drag.column);
				}
				Object.assign(drag.li.style, {
					top: `${drag.top + (drag.minutes * hour) / 60}px`,
					left: "2px",
					width: "calc(100% - 4px)",
					transform: `translateX(${drag.shift}px)`,
				});
				readout(drag.button, at.starts + drag.minutes, at.ends + drag.minutes);
			},

			// A day under the pointer: in the month the cell, marked, and along
			// the all-day row the day column, which the bar slides over to.
			shiftDays(drag, event) {
				const month = drag.column.tagName === "TD";
				const found = month
					? document.elementFromPoint(event.clientX, event.clientY)?.closest("td[data-date]")
					: this.columnAt(event.clientX);
				const day = found && this.$root.contains(found) ? found : null;
				if (day) drag.days = daysBetween(drag.column.dataset.date, day.dataset.date);
				if (!month) {
					const shift = day ? left(day) - left(drag.column) : 0;
					drag.li.style.transform = `translateX(${shift}px)`;
					return;
				}
				if (day === drag.under) return;
				drag.under?.classList.remove(...DROP);
				drag.under = day;
				day?.classList.add(...DROP);
			},

			release() {
				const drag = this.drag;
				if (!drag) return;
				this.drag = null;
				drag.unlisten();
				// A press that never travelled is a click, which the click
				// handlers take from here.
				if (!drag.moved) return;
				this.swallow = true;
				setTimeout(() => (this.swallow = false));
				if (drag.cancelled) return;
				if (!live(drag)) return this.settle(drag);
				if (drag.mode === "create") {
					this.settle(drag);
					const [a, b] = span(drag.from, drag.to);
					this.calendarOpen(slotBody(key, drag.column.dataset.date, a, b));
					return;
				}
				if (!drag.days && !drag.minutes) {
					this.settle(drag);
					return;
				}
				// Left where it was dropped until the response redraws it, so
				// it does not jump back and forth.
				drag.column.parentElement.classList.remove("select-none");
				const change = { days: drag.days, minutes: drag.minutes, resize: drag.mode === "resize" };
				this.post(drag.button, change).then((redrawn) => redrawn || this.settle(drag));
			},

			// keep holds on to a drag Escape cancelled until the pointer is
			// let go, so the click that follows opens nothing.
			cancel({ keep = false } = {}) {
				const drag = this.drag;
				if (!drag) return;
				if (!drag.cancelled) this.settle(drag);
				if (keep && drag.moved) {
					drag.cancelled = true;
					return;
				}
				this.drag = null;
				drag.unlisten();
			},

			// Put back what a drag changed on the page.
			settle(drag) {
				drag.column.parentElement.classList.remove("select-none");
				drag.ghost?.remove();
				drag.under?.classList.remove(...DROP);
				if (!drag.li) return;
				drag.li.style.cssText = drag.css;
				drag.li.classList.remove(...DRAGGING);
				const time = drag.button.querySelector("[data-time]");
				if (time) time.textContent = drag.time;
			},

			keys(event) {
				const step = STEPS[event.key];
				const button = event.target.closest?.("[data-event-id]");
				if (!step || !button || !event.altKey || event.ctrlKey || event.metaKey) return;
				event.preventDefault();
				if (this.moving) return;
				const [days, minutes] = step;
				this.post(button, { days, minutes, resize: event.shiftKey });
			},

			// Whether the calendar came back: a change that is not one, or an
			// answer with no calendar in it, such as a proxy's error page,
			// leaves the page as it was.
			async post(button, change) {
				const fields = shifted(button, change);
				if (!fields) return false;
				const body = new FormData();
				body.set(`${key}-id`, button.dataset.eventId);
				body.set(`${key}-occurrence`, button.dataset.starts);
				for (const [name, value] of Object.entries(fields)) {
					body.set(`${key}-${name}`, value);
				}
				this.moving = true;
				try {
					await this.send(move, body);
				} catch {
					return false;
				} finally {
					this.moving = false;
				}
				return true;
			},
		}),
	);
}

function left(element) {
	return element.getBoundingClientRect().left;
}

// Whether what a drag holds is still on the page: a response that redrew
// the calendar mid-drag has replaced it, and its times are stale.
function live(drag) {
	return drag.column.isConnected && (!drag.button || drag.button.isConnected);
}

function clock(minutes) {
	const hours = String(Math.floor(minutes / 60)).padStart(2, "0");
	return `${hours}:${String(minutes % 60).padStart(2, "0")}`;
}

// The start and end a drag from one minute to another covers: at least a
// snap long, whichever way it was dragged.
function span(from, to) {
	const a = Math.min(from, to);
	return [a, Math.max(from, to, a + SNAP)];
}

// The dialog's fields for a slot, from one minute of a day to another; an
// end at midnight is the next day's first minute.
function slotBody(key, day, from, to) {
	const body = new FormData();
	body.set(`${key}-starts`, day);
	body.set(`${key}-starts_time`, clock(from));
	body.set(`${key}-ends`, to >= DAY ? shiftDay(day, 1) : day);
	body.set(`${key}-ends_time`, clock(to % DAY));
	return body;
}

// When an event is, off its button: the day it starts, and its start and
// end in minutes from that day's midnight, so an end past midnight counts
// on past the day.
function when(button) {
	const [day, starts] = split(button.dataset.starts);
	const [endDay, ends] = split(button.dataset.ends);
	const length = ends + daysBetween(day, endDay) * DAY - starts;
	return {
		day,
		endDay,
		allDay: "allDay" in button.dataset,
		starts,
		ends: starts + length,
		length,
	};
}

function split(stamp) {
	const [day, time = "00:00"] = stamp.split("T");
	const [hours, minutes] = time.split(":").map(Number);
	return [day, hours * 60 + minutes];
}

// How far a move or a resize may go in minutes: the event stays inside its
// day, unless it already ran past midnight, and keeps a snap of length.
function bounds(at, mode) {
	const limit = Math.max(DAY, at.ends);
	if (mode === "resize") return [SNAP - at.length, limit - at.ends];
	return [-at.starts, limit - at.ends];
}

// The fields a change to an event posts, or null for one that would take
// it outside its day or its end before its start.
function shifted(button, { days = 0, minutes = 0, resize = false }) {
	const at = when(button);
	if (at.allDay) {
		if (minutes) return null;
		const starts = resize ? at.day : shiftDay(at.day, days);
		const ends = shiftDay(at.endDay, days);
		return ends < starts ? null : { all_day: "1", starts, ends };
	}
	if (resize && days) return null;
	const limit = Math.max(DAY, at.ends);
	const starts = resize ? at.starts : at.starts + minutes;
	const ends = at.ends + minutes;
	if (starts < 0 || ends > limit || ends < starts + SNAP) return null;
	const day = shiftDay(at.day, resize ? 0 : days);
	return {
		starts: day,
		starts_time: clock(starts),
		ends: shiftDay(day, Math.floor(ends / DAY)),
		ends_time: clock(ends % DAY),
	};
}

// Day arithmetic in UTC, so a day is always twenty-four hours long.
function shiftDay(day, count) {
	const [year, month, date] = day.split("-").map(Number);
	return new Date(Date.UTC(year, month - 1, date + count)).toISOString().slice(0, 10);
}

function daysBetween(from, to) {
	return Math.round((Date.parse(to) - Date.parse(from)) / 864e5);
}

// The time an event shows, rewritten as it is dragged.
function readout(button, starts, ends) {
	const time = button.querySelector("[data-time]");
	if (time) time.textContent = `${clock(starts)} – ${clock(ends % DAY)}`;
}
