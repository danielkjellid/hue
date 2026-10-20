/**
 * The text of a date field: writing a value the way the server does, and
 * reading back what a person typed.
 *
 * Values are ISO text throughout: YYYY-MM-DD, HH:MM, or both joined by T.
 * Nothing here touches the page, so the browser checks can drive it with
 * nothing but a field.
 */

import { DAY, iso, parse, utc, weekday } from "./date-picker.js";

const pad = (n, width = 2) => String(n).padStart(width, "0");

/**
 * The value written with a strftime format, for the directives Formats is
 * likely to hold. %b is the first three letters of the month's name, as
 * Python writes it in English. Any other directive is left as it is.
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
		y: () => day.slice(2, 4),
		m: () => day.slice(5, 7),
		d: () => day.slice(8),
		B: () => names.monthNames[month],
		b: () => names.monthNames[month].slice(0, 3),
		A: () => names.dayNames[wd],
		a: () => names.dayAbbreviations[wd],
		H: () => pad(hour),
		I: () => pad(hour % 12 || 12),
		M: () => pad(minute),
		p: () => (hour < 12 ? "AM" : "PM"),
		"%": () => "%",
	};
	return format.replace(/%(.)/g, (all, c) => fields[c]?.() ?? all);
}

function real(year, month, day) {
	if (year < 1 || year > 9999) return null;
	const at = utc(year, month - 1, day);
	// 2026-02-31 rolls over into March. A day that does not come back as
	// itself is not a day.
	return iso(at).endsWith(`-${pad(month)}-${pad(day)}`) ? iso(at) : null;
}

/**
 * A day from today, tomorrow or yesterday, 2026-10-20, 20.10.2026,
 * 20/10/26, 20 Oct 2026 or Oct 20, 2026, after an optional weekday. Month
 * and weekday names are matched by prefix against the names given, so a
 * framework's translations are read as well as written. monthFirst reads
 * 10/20/2026 as October, for a format that writes it that way.
 */
export function parseDay(text, { monthNames, dayNames, monthFirst, today }) {
	let s = text.trim().toLowerCase();
	const lead = /^(\p{L}+)\.?,?\s+/u.exec(s);
	if (lead && lead[1].length >= 2 && dayNames.some((n) => n.toLowerCase().startsWith(lead[1]))) {
		s = s.slice(lead[0].length);
	}
	const relative = { today: 0, tomorrow: 1, yesterday: -1 }[s];
	if (relative !== undefined) return iso(parse(today) + relative * DAY);

	const named = (word) =>
		word.length >= 3 ? monthNames.findIndex((n) => n.toLowerCase().startsWith(word)) + 1 : 0;
	let m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
	if (m) return real(+m[1], +m[2], +m[3]);
	m = /^(\d{1,2})[./](\d{1,2})[./](\d{2}|\d{4})$/.exec(s);
	if (m) {
		const year = m[3].length === 2 ? 2000 + +m[3] : +m[3];
		return monthFirst ? real(year, +m[1], +m[2]) : real(year, +m[2], +m[1]);
	}
	m = /^(\d{1,2})\.?\s+(\p{L}+)\.?,?\s+(\d{4})$/u.exec(s);
	if (m && named(m[2])) return real(+m[3], named(m[2]), +m[1]);
	m = /^(\p{L}+)\.?\s+(\d{1,2}),?\s+(\d{4})$/u.exec(s);
	if (m && named(m[1])) return real(+m[3], named(m[1]), +m[2]);
	return null;
}

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
 * as the time, so 2026-10-20 14:30 and 20 Oct 2026, 2:30 pm both read.
 * The time is null when only a day was typed.
 */
export function parseMoment(text, options) {
	const day = parseDay(text, options);
	if (day) return { day, time: null };
	const words = text.trim().split(/\s+/);
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
