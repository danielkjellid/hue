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
		dayNames,
	} = config;
	const unavailable = new Set(config.unavailable);
	const closed = new Set(config.closed);
	const markers = new Set(config.markers);
	// Wednesday 14 October 2026, the order Formats.day() writes.
	const name = (day) =>
		`${dayNames[weekday(parse(day))]} ${+day.slice(8)} ${monthNames[+day.slice(5, 7) - 1]} ${day.slice(0, 4)}`;
	const clamp = (day) => (min && day < min ? min : max && day > max ? max : day);

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
			this.focus = this.value[0] ?? clamp(today());
			this.shown = monthOf(this.focus);
		},

		// Focus day, paging only when it falls outside the shown months.
		show(day) {
			const month = monthOf(day);
			if (month < this.shown) this.shown = month;
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
			if (mode !== "range" || !this.value.length) return null;
			const [start, end = this.hover ?? start] = this.value;
			return [start, end].sort();
		},

		cell(m, i) {
			const day = this.dayAt(m, i);
			if (!day) return { selected: "false" };
			const band = this.band();
			const pending = mode === "range" && this.value.length === 1;
			const ends = band && (day === band[0] || day === band[1]);
			const inside = band && day > band[0] && day < band[1];
			const filled =
				mode !== "range" ? this.value.includes(day) : pending ? day === this.value[0] : ends;
			const edge = !band || band[0] === band[1] ? null : day === band[0] ? "start" : day === band[1] ? "end" : null;
			return {
				day,
				number: +day.slice(8),
				tab: disabled ? null : day === this.focus ? 0 : -1,
				label: markers.has(day) ? `${name(day)}, ${markerLabel}` : name(day),
				// Every day of a committed range is selected; only its ends are filled.
				selected: String(Boolean(filled || (!pending && inside))),
				current: day === today() ? "date" : null,
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
					String(Boolean(this.value[0]) && monthOf(this.value[0]) === this.year() * 12 + i),
				":data-current": () => monthOf(today()) === this.year() * 12 + i || null,
				"x-on:click": () => this.chooseMonth(i),
			};
		},

		yearItem(i) {
			return {
				"x-text": () => this.yearAt(i),
				":aria-pressed": () =>
					String(Boolean(this.value[0]) && +this.value[0].slice(0, 4) === this.yearAt(i)),
				":data-current": () => +today().slice(0, 4) === this.yearAt(i) || null,
				"x-on:click": () => this.chooseYear(this.yearAt(i)),
			};
		},

		// n months on, the view and the focused day together, so the tab
		// stop stays in a shown month. The panels' buttons page by 1, 12
		// and 144.
		page(n) {
			if (this.shown + n < FIRST_MONTH || this.shown + n > LAST_MONTH) return;
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

		chooseYear(year) {
			this.shown = year * 12 + (this.shown % 12);
			this.focus = addMonths(this.focus, (year - +this.focus.slice(0, 4)) * 12);
			// On the month being shown, which the year kept.
			this.switchTo("months", () => this.$refs.months.querySelectorAll("[data-item]")[this.shown % 12]);
		},

		focusedCell() {
			return this.$root.querySelector(`[data-date="${this.focus}"]`);
		},

		move(day) {
			const month = monthOf(day);
			if (month < FIRST_MONTH || month > LAST_MONTH) return;
			this.show(day);
			if (mode === "range" && this.value.length === 1) this.hover = day;
			this.$nextTick(() => this.focusedCell()?.focus());
		},

		// Returns whether the pick is complete, for a field that closes
		// once it is.
		select(day) {
			if (disabled || this.isUnavailable(day)) return false;
			this.value = PICK[mode](this.value, day);
			this.hover = null;
			return mode === "single" || (mode === "range" && this.value.length === 2);
		},

		click(event) {
			const day = event.target.closest("[data-date]")?.dataset.date;
			if (!day) return;
			this.show(day);
			this.select(day);
		},

		preview(event) {
			const day = event.target.closest("[data-date]")?.dataset.date;
			if (day && mode === "range" && this.value.length === 1) this.hover = day;
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
