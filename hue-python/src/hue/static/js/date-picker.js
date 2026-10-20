/**
 * hueDatePicker: the APG date grid behind DatePicker.
 *
 * Every day is an ISO YYYY-MM-DD string: the selection, the focused day,
 * min and max. Strings carry no time, so no time zone or DST change can
 * move one, and with four-digit years they sort in date order. Arithmetic
 * goes through UTC milliseconds and back.
 *
 * The cells are drawn by the server, six weeks of seven per month, and
 * each one binds to day(month, index) here. They never come and go, so no
 * x-for scope is half refreshed when the month changes and the roving
 * tabindex is an ordinary binding.
 *
 * A field that opens the grid in a popover spreads datePicker(config) into
 * its own data and wraps select(), which returns true once a pick is
 * complete: one day, or the end of a range.
 */

const DAY = 24 * 60 * 60 * 1000;
// The months date.fromisoformat() accepts on the server.
const FIRST_MONTH = 1 * 12;
const LAST_MONTH = 9999 * 12 + 11;
const FIRST_DAY = "0001-01-01";
const LAST_DAY = "9999-12-31";

// What a pick does to the selection, per mode. Range: the first pick starts
// one, the second ends it, in either order.
const PICK = {
	single: (value, day) => [day],
	range: (value, day) => (value.length === 1 ? [value[0], day].sort() : [day]),
	multiple: (value, day) =>
		value.includes(day)
			? value.filter((each) => each !== day)
			: [...value, day].sort(),
};

// Through setUTCFullYear rather than Date.UTC, which reads a year under
// 100 as the 1900s. The month is 0-based and overflows into the next year.
function utc(year, month, day) {
	const at = new Date(0);
	at.setUTCFullYear(year, month, day);
	return at.getTime();
}

const iso = (at) => new Date(at).toISOString().slice(0, 10);
const parse = (day) => utc(+day.slice(0, 4), +day.slice(5, 7) - 1, +day.slice(8));
const monthOf = (day) => +day.slice(0, 4) * 12 + +day.slice(5, 7) - 1;
const firstOf = (month) => utc(Math.floor(month / 12), month % 12, 1);
// Monday 0, as date.weekday() counts.
const weekday = (at) => (new Date(at).getUTCDay() + 6) % 7;

function today() {
	const now = new Date();
	return iso(utc(now.getFullYear(), now.getMonth(), now.getDate()));
}

// The day of the cell an event happened in, when that cell is root's own:
// a picker inside something else with data-date answers for itself only.
function pickedDay(root, event) {
	const cell = event.target.closest("td[data-date]");
	return cell && root.contains(cell) ? cell.dataset.date : null;
}

// The same day of the month n months on, clamped where it does not fit:
// the 31st pages to the 30th.
function addMonths(day, n) {
	const month = monthOf(day) + n;
	const last = new Date(firstOf(month + 1) - DAY).getUTCDate();
	return iso(firstOf(month) + (Math.min(+day.slice(8), last) - 1) * DAY);
}

export function datePicker(config) {
	const {
		mode,
		months,
		weekStart,
		min,
		max,
		disabled,
		markerLabel,
		monthNames,
		monthNamesInDate,
		dayNames,
	} = config;
	const unavailable = new Set(config.unavailable);
	const closed = new Set(config.closed);
	const markers = new Set(config.markers);
	// Wednesday 14 October 2026, the words and order Formats.day() writes.
	const name = (day) =>
		`${dayNames[weekday(parse(day))]} ${+day.slice(8)} ${monthNamesInDate[+day.slice(5, 7) - 1]} ${day.slice(0, 4)}`;
	const clamp = (day) => (min && day < min ? min : max && day > max ? max : day);
	// Whether every month shown from this first one is one the server takes.
	const fits = (first) => first >= FIRST_MONTH && first + months - 1 <= LAST_MONTH;
	const now = today();
	// The selection as the picker last saw it, so a change from outside,
	// through x-model, can be told from a pick.
	let seen = config.value.join();

	return {
		value: [...config.value],
		// The day holding the roving tabindex, always in a shown month.
		focus: null,
		// The first shown month, as year * 12 + month.
		shown: 0,
		// The end a pending range would get, under the pointer or the keys.
		hover: null,
		level: "days",

		init() {
			this.focus = this.value[0] ?? clamp(now);
			this.shown = Math.min(monthOf(this.focus), LAST_MONTH - months + 1);
			// A value set from outside moves the view to it. Picks are made
			// on a shown month already, and a multiple pick must not page
			// back to the earliest day.
			this.$watch("value", (value) => {
				// x-model can hand over anything; the cells need a list.
				if (!Array.isArray(value)) {
					this.value = [];
					return;
				}
				if (value.join() === seen) return;
				seen = value.join();
				if (value[0]) this.show(value[0]);
			});
		},

		// Focus day, paging only when it falls outside the shown months.
		// The selection as a list, whatever x-model handed over: the
		// bindings read it before the watch above can put a list back.
		days() {
			return Array.isArray(this.value) ? this.value : [];
		},

		show(day) {
			const month = monthOf(day);
			if (month < this.shown) this.shown = Math.min(month, LAST_MONTH - months + 1);
			else if (month > this.shown + months - 1) this.shown = month - months + 1;
			this.focus = day;
		},

		title(m) {
			const month = this.shown + m;
			return `${monthNames[month % 12]} ${Math.floor(month / 12)}`;
		},

		year() {
			return Math.floor(this.shown / 12);
		},

		decade() {
			const first = this.year() - (this.year() % 12);
			return `${first} – ${first + 11}`;
		},

		dayAt(m, i) {
			const first = firstOf(this.shown + m);
			const at = first + (i - ((weekday(first) - weekStart + 7) % 7)) * DAY;
			const day = iso(at);
			return monthOf(day) === this.shown + m ? day : null;
		},

		isUnavailable(day) {
			return (
				(min && day < min) ||
				(max && day > max) ||
				closed.has(weekday(parse(day))) ||
				unavailable.has(day)
			);
		},

		// The range as drawn: committed, or from its start to where the
		// pointer or the keys are.
		band() {
			const value = this.days();
			if (mode !== "range" || !value.length) return null;
			const [start, end = this.hover ?? start] = value;
			return [start, end].sort();
		},

		cell(m, i) {
			const day = this.dayAt(m, i);
			if (!day) return { selected: "false" };
			const value = this.days();
			const band = this.band();
			const pending = mode === "range" && value.length === 1;
			const ends = band && (day === band[0] || day === band[1]);
			const inside = band && day > band[0] && day < band[1];
			const filled =
				mode !== "range" ? value.includes(day) : pending ? day === value[0] : ends;
			let edge = null;
			if (band && band[0] !== band[1]) {
				if (day === band[0]) edge = "start";
				else if (day === band[1]) edge = "end";
			}
			return {
				day,
				number: +day.slice(8),
				tab: disabled ? null : day === this.focus ? 0 : -1,
				label: markers.has(day) ? `${name(day)}, ${markerLabel}` : name(day),
				// Every day of a committed range is selected; only its ends are filled.
				selected: String(Boolean(filled || (!pending && inside))),
				current: day === now ? "date" : null,
				unavailable: this.isUnavailable(day) ? "true" : null,
				filled: filled || null,
				band: edge ?? (inside ? "inside" : null),
				preview: (pending && (ends || inside)) || null,
				marked: markers.has(day) || null,
			};
		},

		day(m, i) {
			const cell = () => this.cell(m, i);
			return {
				":data-date": () => cell().day,
				":tabindex": () => cell().tab,
				":aria-label": () => cell().label,
				":aria-selected": () => cell().selected,
				":aria-current": () => cell().current,
				":aria-disabled": () => cell().unavailable,
				":data-filled": () => cell().filled,
				":data-band": () => cell().band,
				":data-preview": () => cell().preview,
				":data-marked": () => cell().marked,
			};
		},

		number(m, i) {
			return this.cell(m, i).number ?? "";
		},

		yearAt(i) {
			return this.year() - (this.year() % 12) + i;
		},

		// The month and year buttons of the jump panels.
		monthItem(i) {
			return {
				":aria-pressed": () =>
					String(Boolean(this.days()[0]) && monthOf(this.days()[0]) === this.year() * 12 + i),
				":data-current": () => monthOf(now) === this.year() * 12 + i || null,
				":disabled": () => !fits(this.year() * 12 + i) || null,
				"x-on:click": () => this.chooseMonth(i),
			};
		},

		yearItem(i) {
			return {
				"x-text": () => this.yearAt(i),
				":aria-pressed": () =>
					String(Boolean(this.days()[0]) && +this.days()[0].slice(0, 4) === this.yearAt(i)),
				":data-current": () => +now.slice(0, 4) === this.yearAt(i) || null,
				":disabled": () => !fits(this.shown + (this.yearAt(i) - this.year()) * 12) || null,
				"x-on:click": () => this.chooseYear(this.yearAt(i)),
			};
		},

		// n months on, the view and the focused day together, so the tab
		// stop stays in a shown month. The panels' buttons page by 1, 12
		// and 144.
		page(n) {
			if (!fits(this.shown + n)) return;
			this.shown += n;
			this.focus = addMonths(this.focus, n);
		},

		// Hiding the button that has focus would drop focus to the body,
		// which a popover around the grid reads as leaving it. Focus waits
		// on the root while the panels swap.
		switchTo(level, target) {
			this.$root.focus({ preventScroll: true });
			this.level = level;
			this.$nextTick(() => target()?.focus());
		},

		nextLevel() {
			if (this.level === "days") {
				this.switchTo("months", () => this.$refs.monthsTitle);
			} else if (this.level === "months") {
				this.switchTo("years", () => this.$refs.yearsTitle);
			} else {
				this.switchTo("days", () => this.focusedCell());
			}
		},

		chooseMonth(i) {
			this.page(this.year() * 12 + i - this.shown);
			this.switchTo("days", () => this.focusedCell());
		},

		// By whole years through page(), so the focused day moves with the
		// view even when it sits in a later shown month of another year.
		chooseYear(year) {
			this.page((year - this.year()) * 12);
			// On the month being shown, which the year kept.
			this.switchTo("months", () => this.$refs.months.querySelectorAll("[data-item]")[this.shown % 12]);
		},

		focusedCell() {
			return this.$root.querySelector(`[data-date="${this.focus}"]`);
		},

		move(day) {
			// Outside four-digit years toISOString writes a sign ahead of the
			// year, as in +010000-01-01, which sorts before every real day.
			if (day < FIRST_DAY || day > LAST_DAY) return;
			this.show(day);
			if (mode === "range" && this.days().length === 1) this.hover = day;
			this.$nextTick(() => this.focusedCell()?.focus());
		},

		// Returns whether the pick is complete, for a field that closes
		// once it is.
		select(day) {
			if (disabled || this.isUnavailable(day)) return false;
			this.value = PICK[mode](this.days(), day);
			seen = this.value.join();
			this.hover = null;
			return mode === "single" || (mode === "range" && this.value.length === 2);
		},

		click(event) {
			const day = pickedDay(this.$root, event);
			if (!day) return;
			this.show(day);
			this.select(day);
		},

		preview(event) {
			const day = pickedDay(this.$root, event);
			if (day && mode === "range" && this.days().length === 1) this.hover = day;
		},

		key(event) {
			const { key, shiftKey, target } = event;
			if (key === "Escape" && this.level !== "days") {
				// Back to the days, and no further: a dialog around the
				// picker stays open.
				event.stopPropagation();
				this.switchTo("days", () => this.focusedCell());
				return;
			}
			const day = target.dataset?.date;
			if (!day) return;
			const at = parse(day);
			const back = (weekday(at) - weekStart + 7) % 7;
			const steps = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7, Home: -back, End: 6 - back };
			if (key in steps) {
				this.move(iso(at + steps[key] * DAY));
			} else if (key === "PageUp" || key === "PageDown") {
				this.move(addMonths(day, (key === "PageUp" ? -1 : 1) * (shiftKey ? 12 : 1)));
			} else if (key === "Enter" || key === " ") {
				this.select(day);
			} else {
				return;
			}
			event.preventDefault();
		},
	};
}

export function registerDatePickerData(Alpine) {
	Alpine.data("hueDatePicker", datePicker);
}
