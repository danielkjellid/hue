/**
 * Keyboard shortcuts, from anywhere on the page.
 *
 * x-shortcut='["mod+k"]' registers its element for as long as the element is
 * on the page, so a fragment swapped in brings its shortcuts with it and one
 * swapped out takes them away. One listener on the window matches key
 * presses against everything registered and clicks the element that
 * matches, which is the same thing picking it would have done. An element
 * that means something else by its shortcut, such as a palette that opens,
 * cancels the hue:shortcut event it is sent first.
 *
 * A shortcut is steps: "g", "b" is G then B, each within a second of the
 * last. Shortcuts with no modifier in them, the letter ones, are ignored
 * while typing in a field and can be switched off as a whole through
 * $store.shortcuts.letters.
 */

const IS_APPLE = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
const SEQUENCE_MS = 1000;
const STORAGE_KEY = "hue-shortcut-letters";

// The names Kbd draws, as KeyboardEvent.key spells them.
const ALIASES = {
	esc: "escape",
	up: "arrowup",
	down: "arrowdown",
	left: "arrowleft",
	right: "arrowright",
	space: " ",
};

// As aria-keyshortcuts spells them.
const ARIA_KEYS = {
	escape: "Escape",
	arrowup: "ArrowUp",
	arrowdown: "ArrowDown",
	arrowleft: "ArrowLeft",
	arrowright: "ArrowRight",
	" ": "Space",
	enter: "Enter",
	tab: "Tab",
	backspace: "Backspace",
	delete: "Delete",
};

function parse(step) {
	const parts = step.toLowerCase().split("+");
	const key = parts.pop();
	const mods = new Set(parts);
	return {
		key: ALIASES[key] ?? key,
		meta: IS_APPLE && mods.has("mod"),
		ctrl: mods.has("ctrl") || (!IS_APPLE && mods.has("mod")),
		alt: mods.has("alt"),
		shift: mods.has("shift"),
	};
}

const isLetters = (steps) => steps.every((step) => !step.meta && !step.ctrl && !step.alt);

// The physical key for letters and digits, because Option on a Mac turns
// Option-N into a tilde, and the character for everything else.
function keyOf(event) {
	if (/^Key[A-Z]$/.test(event.code)) return event.code.slice(3).toLowerCase();
	if (/^Digit\d$/.test(event.code)) return event.code.slice(5);
	return event.key.toLowerCase();
}

function matches(event, step) {
	// Shift is part of how "?" is typed, so it only has to match exactly for
	// letters and digits, where it means something.
	const shiftMatters = step.shift || /^[a-z0-9]$/.test(step.key);
	return (
		keyOf(event) === step.key &&
		event.metaKey === step.meta &&
		event.ctrlKey === step.ctrl &&
		event.altKey === step.alt &&
		(!shiftMatters || event.shiftKey === step.shift)
	);
}

function editable(target) {
	return (
		target instanceof Element &&
		(target.isContentEditable || target.closest("input, textarea, select") !== null)
	);
}

function aria(step) {
	const keys = [];
	if (step.ctrl) keys.push("Control");
	if (step.meta) keys.push("Meta");
	if (step.alt) keys.push("Alt");
	if (step.shift) keys.push("Shift");
	keys.push(ARIA_KEYS[step.key] ?? step.key.toUpperCase());
	return keys.join("+");
}

function readLetters() {
	try {
		return localStorage.getItem(STORAGE_KEY) !== "off";
	} catch {
		return true;
	}
}

export function registerShortcuts(Alpine) {
	const registered = new Set();
	let pressed = [];

	// $store.shortcuts.letters is the switch WCAG 2.1.4 asks for. Bind a Switch
	// in an app's settings to it with x_model; it is remembered in this
	// browser whichever way it is set.
	Alpine.store("shortcuts", { letters: readLetters() });
	Alpine.effect(() => {
		const on = Alpine.store("shortcuts").letters;
		try {
			localStorage.setItem(STORAGE_KEY, on ? "on" : "off");
		} catch {}
	});

	// x-shortcut binds the keys to its element. x-shortcut.describe only says
	// what they are, through aria-keyshortcuts, for a visible row whose keys
	// are bound somewhere else: the page binds a registry's shortcuts once,
	// and the palette and menus that show them must not bind them again.
	Alpine.directive("shortcut", (el, { expression, modifiers }, { evaluate, cleanup }) => {
		const steps = evaluate(expression).map(parse);
		if (modifiers.includes("describe")) {
			// A sequence has no way to be written in aria-keyshortcuts.
			if (steps.length === 1) el.setAttribute("aria-keyshortcuts", aria(steps[0]));
			return;
		}
		const entry = { el, steps };
		registered.add(entry);
		cleanup(() => registered.delete(entry));
	});

	window.addEventListener("keydown", (event) => {
		if (event.repeat || ["Shift", "Meta", "Control", "Alt"].includes(event.key)) return;
		const now = event.timeStamp;
		if (pressed.length && now - pressed.at(-1).at > SEQUENCE_MS) pressed = [];
		// As long as the longest sequence anyone would type, and no longer.
		pressed = [...pressed.slice(-7), { event, at: now }];
		const typing = editable(event.target);
		const letters = Alpine.store("shortcuts").letters;

		const found = [...registered].filter(({ el, steps }) => {
			if (steps.length > pressed.length) return false;
			if (el.getAttribute("aria-disabled") === "true") return false;
			if (isLetters(steps) && (typing || !letters)) return false;
			const recent = pressed.slice(-steps.length);
			return steps.every((step, index) => matches(recent[index].event, step));
		});
		if (!found.length) return;

		// Two elements on one page claiming the same keys: the first one in
		// the document has them.
		const { el } = found.sort((a, b) =>
			a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1,
		)[0];
		event.preventDefault();
		pressed = [];
		const proceed = el.dispatchEvent(new CustomEvent("hue:shortcut", { cancelable: true }));
		if (proceed) el.click();
	});
}
