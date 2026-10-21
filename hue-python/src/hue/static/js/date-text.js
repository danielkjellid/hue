/**
 * The text of a date field: writing a value the way the server does, and
 * reading back what a person typed.
 *
 * Values are ISO text throughout: YYYY-MM-DD, HH:MM, or both joined by T.
 * Nothing here touches the page, so the browser checks can drive it with
 * nothing but a field.
 */

import { DAY, iso, parse, utc, weekday } from "./date-picker.js";

export const pad = (n) => String(n).padStart(2, "0");

/**
 * The value written with a strftime format, for the directives Formats
 * spells out itself and written the way it writes them, names included.
 * The date fields refuse to render with a format this cannot write or
 * the readers below cannot read back.
 */
export function strftime(format, value, names) {
	const [day, time] = value.includes("T")
		? value.split("T")
		: value.includes(":")
			? [null, value]
			: [value, null];
	const month = day && +day.slice(5, 7) - 1;
	const wd = day && weekday(parse(day));
	const [hour, minute] = time ? time.split(":").map(Number) : [0, 0];
	const fields = {
		Y: () => day.slice(0, 4),
		m: () => day.slice(5, 7),
		"-m": () => String(month + 1),
		d: () => day.slice(8),
		"-d": () => String(+day.slice(8)),
		e: () => String(+day.slice(8)).padStart(2, " "),
		B: () => names.monthNames[month],
		b: () => names.monthAbbreviations[month],
		A: () => names.dayNames[wd],
		a: () => names.dayAbbreviations[wd],
		H: () => pad(hour),
		I: () => pad(hour % 12 || 12),
		"-I": () => String(hour % 12 || 12),
		M: () => pad(minute),
		p: () => (hour < 12 ? "AM" : "PM"),
		"%": () => "%",
	};
	return format.replace(/%(-?.)/g, (all, c) => fields[c]?.() ?? all);
}

function real(year, month, day) {
	if (year < 1 || year > 9999) return null;
	const at = utc(year, month - 1, day);
	// 2026-02-31 rolls over into March. A day that does not come back as
	// itself is not a day.
	return iso(at).endsWith(`-${pad(month)}-${pad(day)}`) ? iso(at) : null;
}

// Names compared as typed: any case, and without the dot an abbreviation
// may end in, since the patterns below read past one.
const plain = (name) => name.toLowerCase().replace(/\.$/, "");

/**
 * The month a word names, 1 to 12: an exact name or abbreviation, or else
 * the start of only one month's. 0 when it names none, or more than one,
 * as "jui" does in French until the abbreviation says June.
 */
function monthOf(word, { monthNames, monthAbbreviations = [] }) {
	const names = [...monthNames, ...monthAbbreviations].map(plain);
	const months = (match) => new Set(names.flatMap((name, i) => (match(name) ? [(i % 12) + 1] : [])));
	let found = months((name) => name === word);
	if (!found.size && word.length >= 3) found = months((name) => name.startsWith(word));
	return found.size === 1 ? [...found][0] : 0;
}

const isWeekday = (word, { dayNames, dayAbbreviations = [] }) =>
	word.length >= 2 && [...dayNames, ...dayAbbreviations].some((name) => plain(name).startsWith(word));

// 26 is the year within 50 of today's that ends in 26.
function century(year, today) {
	const now = +today.slice(0, 4);
	const near = now - (now % 100) + year;
	return near > now + 50 ? near - 100 : near < now - 50 ? near + 100 : near;
}

// A month or weekday name: letters, their marks, the zero-width non-joiner
// and joiner that Persian, Hindi, Kannada and Malayalam write inside a word,
// and the direction marks Sorani writes before one.
const NAME = String.raw`[\p{L}\p{M}\u200C-\u200F]+`;

function readDay(text, options) {
	// 2026. 10. 20. and 20.10.2026. end in a dot.
	const s = text.replace(/\.$/, "");
	const relative = { today: 0, tomorrow: 1, yesterday: -1 }[s];
	if (relative !== undefined) return iso(parse(options.today) + relative * DAY);
	let m = /^(\d{4})[-./]\s*(\d{1,2})[-./]\s*(\d{1,2})$/.exec(s);
	if (m) return real(+m[1], +m[2], +m[3]);
	// Never ISO, which the pattern above has already read.
	m = /^(\d{1,2})[-./]\s*(\d{1,2})[-./]\s*(\d{2}|\d{4})$/.exec(s);
	if (m) {
		const year = m[3].length === 2 ? century(+m[3], options.today) : +m[3];
		return options.monthFirst ? real(year, +m[1], +m[2]) : real(year, +m[2], +m[1]);
	}
	m = new RegExp(String.raw`^(\d{1,2})\.?\s+(${NAME})\.?,?\s+(\d{4})$`, "u").exec(s);
	if (m && monthOf(m[2], options)) return real(+m[3], monthOf(m[2], options), +m[1]);
	m = new RegExp(String.raw`^(${NAME})\.?\s+(\d{1,2}),?\s+(\d{4})$`, "u").exec(s);
	if (m && monthOf(m[1], options)) return real(+m[3], monthOf(m[1], options), +m[2]);
	return null;
}

/**
 * A day from today, tomorrow or yesterday, 2026-10-20, 20.10.2026,
 * 20-10-2026, 20/10/26, 20 Oct 2026 or Oct 20, 2026, after an optional
 * weekday. Month and weekday names are matched against the names given,
 * so a framework's translations are read as well as written. monthFirst
 * reads 10/20/2026 as October, for a format that writes it that way. A
 * leading word is only taken for a weekday when the text does not read
 * with it, since "mar" is martes and marzo both. date_input.py mirrors
 * these patterns, and those of parseTime and parseMoment, to refuse a
 * format whose text they would not read.
 */
export function parseDay(text, options) {
	const s = text.trim().toLowerCase();
	const lead = new RegExp(String.raw`^(${NAME})\.?,?\s+`, "u").exec(s);
	return (
		readDay(s, options) ??
		(lead && isWeekday(lead[1], options) ? readDay(s.slice(lead[0].length), options) : null)
	);
}

/**
 * Whether a format writes the month, then the day, then the year, so that
 * 10/20/2026 typed in its field is October. ISO puts the year first, and
 * says nothing about how someone types day.month.year.
 */
export const monthFirst = (format) => /%-?[mbB].*%(?:-?d|e).*%Y/.test(format);

/**
 * HH:MM from 14:30, 14.30, 1430, 2:30 pm or 9a.
 */
export function parseTime(text) {
	const m = /^(\d{1,2})(?:[:.]?(\d{2}))?\s*(am|pm|a|p)?$/.exec(text.trim().toLowerCase());
	if (!m) return null;
	let hour = +m[1];
	const minute = +(m[2] ?? 0);
	if (m[3]) {
		if (hour < 1 || hour > 12) return null;
		hour = (hour % 12) + (m[3][0] === "p" ? 12 : 0);
	}
	return hour < 24 && minute < 60 ? `${pad(hour)}:${pad(minute)}` : null;
}

/**
 * A day and, when one follows it, a time: the last word or two are tried
 * as the time, so 2026-10-20 14:30, 2026-10-20T14:30 and 20 Oct 2026,
 * 2:30 pm all read. The time is null when only a day was typed.
 */
export function parseMoment(text, options) {
	const day = parseDay(text, options);
	if (day) return { day, time: null };
	// The submitted value, 2026-10-20T14:30, reads back too.
	const words = text.trim().replace(/^(\d{4}-\d{1,2}-\d{1,2})T/i, "$1 ").split(/\s+/);
	for (const n of [1, 2]) {
		const time = parseTime(words.slice(-n).join(" "));
		const rest = parseDay(words.slice(0, -n).join(" ").replace(/,$/, ""), options);
		if (time && rest) return { day: rest, time };
	}
	return null;
}

/**
 * The two ends of a typed range, split on a dash with space around it, an
 * en or em dash, or "to". A single hyphen is part of an ISO day.
 */
export function splitRange(text) {
	const parts = text.trim().split(/\s+(?:-|to)\s+|\s*[\u2013\u2014]\s*/);
	return parts.length === 2 ? parts : null;
}
