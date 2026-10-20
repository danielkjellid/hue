/**
 * hueDateInput: a text field with a month grid, a time list or both in a
 * popover, behind DateInput, DateTimeInput and TimeInput.
 *
 * committed is the value, as the ISO text submitted under the field's
 * name: days, a day and a time joined by T, or a time. The grid's own
 * value is what it draws, which for a range is the pick waiting for Apply.
 * The text is for people: written with the server's formats, and read back
 * by date-text.js on Enter and on blur.
 *
 * The grid is hueDatePicker's, spread in. Its select() is wrapped, so a
 * pick commits, and its key() is wrapped, so Escape closes the popover.
 */

import { DAY, datePicker, dayName, iso, parse, today, utc } from "./date-picker.js";
import { monthFirst, parseDay, parseMoment, parseTime, splitRange, strftime } from "./date-text.js";

const pad = (n) => String(n).padStart(2, "0");
const add = (day, n) => iso(parse(day) + n * DAY);
// The last day of the month n months after day's: day 0 of the one after.
const monthEnd = (day, n) => iso(utc(+day.slice(0, 4), +day.slice(5, 7) + n, 0));
const monthStart = (day, n) => add(monthEnd(day, n - 1), 1);

// The ranges behind DateInput's presets, in the order the server draws
// their labels, around today.
const PRESETS = [
	(t) => [t, t],
	(t) => [add(t, -1), add(t, -1)],
	(t) => [add(t, -6), t],
	(t) => [add(t, -29), t],
	(t) => [monthStart(t, 0), monthEnd(t, 0)],
	(t) => [monthStart(t, -1), monthEnd(t, -1)],
	(t) => [t, add(t, 6)],
];

// Where the time list opens when there is no time yet.
const MORNING = "09:00";

export function dateInput(config) {
	const { kind, formats, step, inert } = config;
	const picker = datePicker({
		...config,
		mode: kind === "range" || kind === "multiple" ? kind : "single",
	});
	const write = (value, format) => strftime(format, value, config);
	const writeDay = (day) => write(day, formats.date);
	const reading = () => ({
		...config,
		// The field's own format: a DateTimeInput's day is written by
		// its datetime, whatever the date format says.
		monthFirst: monthFirst(kind === "datetime" ? formats.datetime : formats.date),
		today: today(),
	});
	const example = () => {
		const t = today();
		return {
			range: `${writeDay(t)} \u2013 ${writeDay(add(t, 7))}`,
			datetime: write(`${t}T14:30`, formats.datetime),
			time: write("14:30", formats.time),
		}[kind] ?? writeDay(t);
	};

	return {
		...picker,
		open: false,
		committed: config.committed,
		text: "",
		error: config.error,
		// The time option holding the roving tabindex.
		slot: null,

		init() {
			this.sync();
			picker.init.call(this);
			// A parent's x-model arrives here.
			this.$watch("committed", () => this.sync());
		},

		sync() {
			this.text = this.display();
			this.value = this.days();
		},

		// What the grid draws for the committed value.
		days() {
			if (kind === "time") return [];
			if (kind === "datetime") return this.committed.slice(0, 1).map((v) => v.slice(0, 10));
			return [...this.committed];
		},

		time() {
			const [value] = this.committed;
			return (kind === "datetime" ? value?.slice(11) : value) ?? null;
		},

		display() {
			const [first, last] = this.committed;
			if (!first || kind === "multiple") return "";
			if (kind === "range") return last ? `${writeDay(first)} \u2013 ${writeDay(last)}` : "";
			if (kind === "datetime") return write(first, formats.datetime);
			if (kind === "time") return write(first, formats.time);
			return writeDay(first);
		},

		dayText(day) {
			return writeDay(day);
		},

		removeLabel(day) {
			return `Remove ${dayName(day, config.dayNames, config.monthNames)}`;
		},

		// The text as values, or null when it reads as nothing.
		read(text) {
			if (kind === "time") {
				const time = parseTime(text);
				return time && [time];
			}
			if (kind === "datetime") {
				const moment = parseMoment(text, reading());
				return moment && [`${moment.day}T${moment.time ?? this.time() ?? MORNING}`];
			}
			if (kind === "range") {
				const ends = splitRange(text)?.map((part) => parseDay(part, reading()));
				return ends?.every(Boolean) ? ends.sort() : null;
			}
			const day = parseDay(text, reading());
			return day && [day];
		},

		// Why the values are refused, or an empty string.
		check(values) {
			if (kind === "time") return "";
			for (const day of values.map((v) => v.slice(0, 10))) {
				if (config.min && day < config.min) return `Choose a date on or after ${writeDay(config.min)}.`;
				if (config.max && day > config.max) return `Choose a date on or before ${writeDay(config.max)}.`;
				if (this.isUnavailable(day)) return `${writeDay(day)} is not available.`;
			}
			return "";
		},

		commit(values) {
			this.committed = values;
			this.refuseText("");
			this.sync();
			// After the submitted fields are redrawn, so a listener reads
			// the new value from the form.
			this.$nextTick(() => this.$refs.input.dispatchEvent(new Event("change", { bubbles: true })));
		},

		// Text that is not the value holds the form back, as a browser's
		// own field does, rather than let it submit the old value.
		refuseText(message) {
			this.error = message || null;
			this.$refs.input.setCustomValidity(message);
		},

		// Returns whether there was anything to read: unchanged text is
		// left alone, so a format this cannot read still survives a blur.
		commitText() {
			const text = this.text.trim();
			if (text === this.display().trim()) {
				// Typed back to the value, so its refusal is over.
				if (this.$refs.input.validity.customError) this.refuseText("");
				return false;
			}
			if (!text) {
				this.commit([]);
				return true;
			}
			const values = this.read(text);
			const refused = values ? this.check(values) : `Could not read "${text}". Try ${example()}.`;
			if (refused) {
				this.refuseText(refused);
			} else if (kind === "multiple") {
				this.commit([...new Set([...this.committed, ...values])].sort());
			} else {
				this.commit(values);
			}
			return true;
		},

		expand() {
			if (inert || this.open) return;
			this.value = this.days();
			this.hover = null;
			this.level = "days";
			// The grid's own start: the first day of the value, or today.
			picker.init.call(this);
			const options = this.slots();
			const wanted = this.time() ?? MORNING;
			this.slot = (options.find((o) => o.dataset.time >= wanted) ?? options[0])?.dataset.time ?? null;
			this.open = true;
			this.$nextTick(() => {
				this.centreSlot();
				(kind === "time" ? this.slotOption() : this.focusedCell())?.focus({ preventScroll: true });
			});
		},

		// Focus goes back to the field first: hiding the popover while
		// something inside it has focus would drop focus to the body.
		close() {
			this.$refs.input.focus();
			this.dismiss();
		},

		// A click outside, or focus gone elsewhere: focus is already where
		// it should be. A range waiting for Apply is dropped.
		dismiss() {
			this.open = false;
			this.value = this.days();
			// A grid left on its months would take the next Escape.
			this.level = "days";
		},

		toggle() {
			if (this.open) this.close();
			else this.expand();
		},

		leave(event) {
			if (this.open && event.relatedTarget && !this.$root.contains(event.relatedTarget)) this.dismiss();
		},

		select(day) {
			const done = picker.select.call(this, day);
			if (kind === "multiple" && this.value.join() !== this.committed.join()) {
				this.commit([...this.value]);
			} else if (done && kind === "single") {
				this.commit([day]);
				this.close();
			} else if (done && kind === "datetime") {
				this.commit([`${day}T${this.time() ?? MORNING}`]);
			}
			return done;
		},

		apply() {
			const refused = this.check(this.value);
			if (refused) {
				this.error = refused;
				return;
			}
			this.commit([...this.value]);
			this.close();
		},

		summary() {
			const [start, end] = this.value;
			if (!start) return "Pick a start date";
			if (!end) return "Pick an end date";
			const count = Math.round((parse(end) - parse(start)) / DAY) + 1;
			return `${writeDay(start)} \u2013 ${writeDay(end)}, ${count} ${count === 1 ? "day" : "days"}`;
		},

		preset(i) {
			const range = () => PRESETS[i](today());
			return {
				":aria-pressed": () => String(this.value.join() === range().join()),
				":disabled": () => Boolean(this.check(range())),
				"x-on:click": () => {
					this.value = range();
					this.hover = null;
					this.show(this.value[0]);
				},
			};
		},

		slots() {
			return [...(this.$refs.times?.querySelectorAll("[data-time]") ?? [])];
		},

		slotOption() {
			return this.slots().find((o) => o.dataset.time === this.slot);
		},

		centreSlot() {
			const list = this.$refs.times;
			const option = this.slotOption();
			if (list && option) list.scrollTop = option.offsetTop - list.clientHeight / 2 + option.offsetHeight / 2;
		},

		slotItem(time) {
			return {
				":tabindex": () => (time === this.slot ? 0 : -1),
				":aria-selected": () => String(time === this.time()),
				"x-on:click": () => this.pickTime(time),
			};
		},

		pickTime(time) {
			this.slot = time;
			if (kind === "time") {
				this.commit([time]);
				this.close();
				return;
			}
			const day = this.days()[0] ?? today();
			const refused = this.check([day]);
			if (refused) this.error = refused;
			else this.commit([`${day}T${time}`]);
		},

		// Now, rounded up to the next step of the list.
		now() {
			const at = new Date();
			let minutes = Math.ceil((at.getHours() * 60 + at.getMinutes()) / step) * step;
			let day = today();
			// The list starts again at midnight, which a step that does
			// not divide the day would otherwise skip past.
			if (minutes >= 1440) {
				minutes = 0;
				day = add(day, 1);
			}
			const time = `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`;
			const refused = this.check([day]);
			if (refused) {
				this.error = refused;
				return;
			}
			this.commit([`${day}T${time}`]);
			this.show(day);
			this.slot = this.slots().find((o) => o.dataset.time >= time)?.dataset.time ?? this.slot;
			this.$nextTick(() => this.centreSlot());
		},

		removeDay(day) {
			// The button pressed goes with its chip, so focus goes first.
			this.$refs.input.focus();
			this.commit(this.committed.filter((each) => each !== day));
		},

		inputKey(event) {
			if (event.key === "Enter") {
				// Unchanged text leaves Enter to submit the form.
				if (this.commitText()) event.preventDefault();
			} else if (event.key === "ArrowDown" && !inert) {
				event.preventDefault();
				this.commitText();
				this.expand();
			}
		},

		slotKey(event) {
			const options = this.slots();
			const at = options.indexOf(event.target);
			const to = { ArrowUp: at - 1, ArrowDown: at + 1, Home: 0, End: options.length - 1 }[event.key];
			if (to !== undefined) {
				const next = options[Math.min(Math.max(to, 0), options.length - 1)];
				this.slot = next.dataset.time;
				next.focus();
			} else if (event.key === "Enter" || event.key === " ") {
				this.pickTime(event.target.dataset.time);
			} else {
				return;
			}
			event.preventDefault();
		},

		key(event) {
			// The field's own keys reach here too, and a closed popover
			// has nothing to say about them.
			if (!this.open) return;
			// Back to the days first when the grid is on its month or year
			// panel; that is the grid's own Escape.
			if (event.key === "Escape" && this.open && this.level === "days") {
				// Only the popover closes, not a dialog the field sits in.
				event.preventDefault();
				event.stopPropagation();
				this.close();
			} else if (event.target.dataset?.time) {
				this.slotKey(event);
			} else {
				picker.key.call(this, event);
			}
		},
	};
}

export function registerDateInputData(Alpine) {
	Alpine.data("hueDateInput", dateInput);
}
