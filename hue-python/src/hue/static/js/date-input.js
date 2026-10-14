/**
 * hueDateInput: the month a DateInput picks a day from.
 *
 * Three things are state: whether the panel is open, the month shown, and
 * the day holding the roving tabindex. The grid is derived from those and
 * from the field's value each time it is drawn, so nothing is kept twice.
 *
 * A day is a UTC midnight in milliseconds, so adding a day is adding a day
 * whatever the local clock does around a DST change. Only today is read
 * from the local clock, because that is the reader's today.
 */

const DAY = 24 * 60 * 60 * 1000;

// Through setUTCFullYear rather than Date.UTC, which reads a year under
// 100 as the 1900s.
function utc(year, month, day) {
	const at = new Date(0);
	at.setUTCFullYear(year, month, day);
	return at.getTime();
}

// The years date.fromisoformat() accepts on the server, so a day that is
// picked here is a day there.
const FIRST = utc(1, 0, 1);
const LAST = utc(9999, 11, 31);

function parse(text) {
	const found = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text ?? "");
	if (!found) return null;
	const [year, month, day] = found.slice(1).map(Number);
	const at = utc(year, month - 1, day);
	const back = new Date(at);
	// 2026-02-31 rolls over to March; a value that does not round-trip is
	// not a date.
	const real =
		back.getUTCFullYear() === year &&
		back.getUTCMonth() === month - 1 &&
		back.getUTCDate() === day;
	return real && at >= FIRST && at <= LAST ? at : null;
}

function iso(at) {
	return new Date(at).toISOString().slice(0, 10);
}

// Monday 0, as date.weekday() counts and as weekStart is handed over.
function weekday(at) {
	return (new Date(at).getUTCDay() + 6) % 7;
}

function today() {
	const now = new Date();
	return utc(now.getFullYear(), now.getMonth(), now.getDate());
}

export function registerDateInputData(Alpine) {
	Alpine.data("hueDateInput", (weekStart, months, days) => ({
		open: false,
		shown: { y: 1970, m: 1 },
		focused: null,

		get heading() {
			return `${months[this.shown.m - 1]} ${this.shown.y}`;
		},

		// Six weeks of seven, always, so the panel keeps its height from
		// month to month. The offset of the first is the same sum week_of()
		// does in _days.py: how far the first falls after the week start.
		get weeks() {
			const first = utc(this.shown.y, this.shown.m - 1, 1);
			const start = first - ((weekday(first) - weekStart + 7) % 7) * DAY;
			const now = today();
			const selected = parse(this.$refs.input.value);
			const rows = [];
			for (let row = 0; row < 6; row++) {
				const week = [];
				for (let col = 0; col < 7; col++) {
					const at = start + (row * 7 + col) * DAY;
					const on = new Date(at);
					const day = on.getUTCDate();
					const month = on.getUTCMonth() + 1;
					const year = on.getUTCFullYear();
					week.push({
						iso: iso(at),
						day,
						outside: month !== this.shown.m,
						today: at === now,
						selected: at === selected,
						// The order Formats.day() writes, whatever the language.
						label: `${days[weekday(at)]} ${day} ${months[month - 1]} ${year}`,
					});
				}
				rows.push(week);
			}
			return rows;
		},

		toggle() {
			if (this.open) this.close();
			else this.show();
		},

		// Opens on the field's day, or on today when it holds none or
		// something that is not a day.
		show() {
			const seed = parse(this.$refs.input.value) ?? today();
			this.visit(seed);
			this.open = true;
			this.$nextTick(() => this.focusDay());
		},

		// Focus goes back to the field first: hiding the panel while a day
		// inside it has focus would drop focus to the body.
		close() {
			this.$refs.input.focus();
			this.open = false;
		},

		// A click outside: focus is wherever the click landed, so nothing
		// to put back.
		dismiss() {
			this.open = false;
		},

		// Focus moving somewhere outside the component closes it, which is
		// what lets Tab walk on to the next field.
		leave(event) {
			if (!this.$root.contains(event.relatedTarget)) this.open = false;
		},

		pick(day) {
			const input = this.$refs.input;
			input.value = day;
			input.dispatchEvent(new Event("input", { bubbles: true }));
			input.dispatchEvent(new Event("change", { bubbles: true }));
			this.close();
		},

		// The month n away, with the day of the month kept where it fits
		// and clamped where it does not: the 31st pages to the 30th. Focus
		// stays where it was, on the button that was pressed.
		page(n) {
			const { y, m } = this.shown;
			const last = new Date(utc(y, m - 1 + n + 1, 0)).getUTCDate();
			const day = Math.min(Number(this.focused.slice(8)), last);
			this.visit(utc(y, m - 1 + n, day));
			this.$nextTick(() => this.rove());
		},

		// n days from the focused one, following it into the next month.
		move(n) {
			this.visit(parse(this.focused) + n * DAY);
			this.$nextTick(() => this.focusDay());
		},

		visit(at) {
			if (at < FIRST || at > LAST) return;
			const on = new Date(at);
			this.focused = iso(at);
			this.shown = { y: on.getUTCFullYear(), m: on.getUTCMonth() + 1 };
		},

		// The roving tabindex, set by hand once the rows are drawn. Alpine
		// refreshes the nested loops' scopes one cell at a time, so a binding
		// on the button that compares its cell with the focused day runs
		// against a half-refreshed grid and marks the wrong button when the
		// month changes.
		rove() {
			for (const was of this.$root.querySelectorAll('[data-date][tabindex="0"]')) {
				was.tabIndex = -1;
			}
			const day = this.$root.querySelector(`[data-date="${this.focused}"]`);
			if (day) day.tabIndex = 0;
			return day;
		},

		focusDay() {
			this.rove()?.focus();
		},

		// The APG date picker keys. Escape is not here: CLOSE_ON_ESCAPE on
		// the root handles it, and Tab is left to the browser.
		key(event) {
			const { key, shiftKey, target } = event;
			const steps = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
			if (key in steps) {
				this.move(steps[key]);
			} else if (key === "PageUp" || key === "PageDown") {
				this.page((key === "PageUp" ? -1 : 1) * (shiftKey ? 12 : 1));
				this.$nextTick(() => this.focusDay());
			} else if (key === "Home" || key === "End") {
				const offset = (weekday(parse(this.focused)) - weekStart + 7) % 7;
				this.move(key === "Home" ? -offset : 6 - offset);
			} else if ((key === "Enter" || key === " ") && target.dataset.date) {
				this.pick(target.dataset.date);
			} else {
				return;
			}
			event.preventDefault();
		},
	}));
}
