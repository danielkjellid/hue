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
 * last. While someone types in a field only a chord with Command or Control
 * runs. Shortcuts without mod, ctrl or alt can be switched off as a whole
 * through $store.shortcuts.letters, and while a modal is open none run
 * outside it.
 */

const IS_APPLE = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
const SEQUENCE_MS = 1000;
const STORAGE_KEY = "hue-shortcut-letters";

// Each key with a name, as hue.shortcuts writes it, mapped to how
// KeyboardEvent.key spells it and how aria-keyshortcuts does. Python refuses
// every other name, so a single character or a function key is all that
// reaches here besides these.
const NAMED = {
	esc: ["escape", "Escape"],
	enter: ["enter", "Enter"],
	tab: ["tab", "Tab"],
	space: [" ", "Space"],
	backspace: ["backspace", "Backspace"],
	delete: ["delete", "Delete"],
	up: ["arrowup", "ArrowUp"],
	down: ["arrowdown", "ArrowDown"],
	left: ["arrowleft", "ArrowLeft"],
	right: ["arrowright", "ArrowRight"],
	home: ["home", "Home"],
	end: ["end", "End"],
	pageup: ["pageup", "PageUp"],
	pagedown: ["pagedown", "PageDown"],
};

function parse(step) {
	const parts = step.split("+");
	const name = parts.pop();
	const mods = new Set(parts);
	return {
		key: NAMED[name]?.[0] ?? name,
		aria: NAMED[name]?.[1] ?? name.toUpperCase(),
		meta: IS_APPLE && mods.has("mod"),
		ctrl: mods.has("ctrl") || (!IS_APPLE && mods.has("mod")),
		alt: mods.has("alt"),
		shift: mods.has("shift"),
	};
}

// Character keys, in WCAG 2.1.4's sense: no modifier that makes a press
// deliberate. These are what the off switch turns off.
const isLetters = (steps) => steps.every((step) => !step.meta && !step.ctrl && !step.alt);

// What can run while someone types in a field: only a chord with Command or
// Control, since Option and Alt also type characters, Option-C a "ç".
const isCommand = (steps) => steps.every((step) => step.meta || step.ctrl);

// The character typed, which follows the keyboard layout: on AZERTY the key
// that types a is the one "a" means. Two cases fall back to the key that was
// pressed. Option on a Mac composes a character, so Option-N arrives as a
// tilde. A layout without Latin letters types its own, so Control-K on a
// Russian keyboard arrives as "л".
function keyOf(event) {
	const typed = event.key.toLowerCase();
	// AltGr types a character of its own, and Windows reports it as Control
	// and Alt held together: "ą" is AltGr-A. Read by the key it was typed on,
	// it would look like ctrl+alt+a. Not on a Mac, where Option is the key
	// that composes and is handled below.
	if (!IS_APPLE && event.getModifierState?.("AltGraph")) return typed;
	const composed = IS_APPLE && event.altKey;
	if (composed || (typed.length === 1 && !/^[\x20-\x7e]$/.test(typed))) {
		if (/^Key[A-Z]$/.test(event.code)) return event.code.slice(3).toLowerCase();
		if (/^Digit\d$/.test(event.code)) return event.code.slice(5);
	}
	return typed;
}

// The open modal, if there is one. Shortcuts wait while it is up, since
// running one would act on the page underneath it, except in a palette,
// whose job is to list them.
function blockingModal() {
	return [...document.querySelectorAll('[aria-modal="true"]')].find(
		(modal) =>
			!modal.hasAttribute("data-shortcuts") &&
			// checkVisibility is missing before Safari 17.4.
			(modal.checkVisibility?.() ?? modal.offsetParent !== null),
	);
}

function matches(event, step) {
	// Shift is how a digit or a symbol becomes another character, and Python
	// refuses shift on those, so it only has to match for letters and named
	// keys, where shift+tab is not tab.
	const shiftMatters = step.key.length > 1 || /^[a-z]$/.test(step.key);
	return (
		keyOf(event) === step.key &&
		event.metaKey === step.meta &&
		event.ctrlKey === step.ctrl &&
		event.altKey === step.alt &&
		(!shiftMatters || event.shiftKey === step.shift)
	);
}

// Somewhere that takes typing: a text field, and a control whose letters
// jump to an option, as a Select, a Combobox and a menu all do.
const TYPED_INTO = 'input, textarea, select, [role="combobox"], [role="listbox"], [role="menu"]';

function editable(target) {
	return (
		target instanceof Element &&
		(target.isContentEditable || target.closest(TYPED_INTO) !== null)
	);
}

function aria(step) {
	const keys = [];
	if (step.ctrl) keys.push("Control");
	if (step.meta) keys.push("Meta");
	if (step.alt) keys.push("Alt");
	if (step.shift) keys.push("Shift");
	keys.push(step.aria);
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
	// browser whichever way it is set. apple is here for Kbd, which draws mod
	// as Command or Ctrl by the same test the keys are matched by.
	Alpine.store("shortcuts", { letters: readLetters(), apple: IS_APPLE });
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
		// Composing, the keys are spelling a character in an input method,
		// not asking for anything; and a press something else handled is
		// its, not ours.
		if (event.isComposing || event.repeat || event.defaultPrevented) return;
		// Autofill sends keydowns with no key at all.
		if (typeof event.key !== "string") return;
		if (["Shift", "Meta", "Control", "Alt"].includes(event.key)) return;
		const entries = [...registered];
		const longest = Math.max(0, ...entries.map(({ steps }) => steps.length));
		const now = event.timeStamp;
		if (pressed.length && now - pressed.at(-1).at > SEQUENCE_MS) pressed = [];
		// As many presses as the longest shortcut has, and no more.
		pressed = [...pressed, { event, at: now }].slice(-Math.max(longest, 1));
		const typing = editable(event.target);
		const letters = Alpine.store("shortcuts").letters;

		const matched = entries.filter(({ steps }) => {
			if (steps.length > pressed.length) return false;
			if (typing && !isCommand(steps)) return false;
			if (isLetters(steps) && !letters) return false;
			const recent = pressed.slice(-steps.length);
			return steps.every((step, index) => matches(recent[index].event, step));
		});
		if (!matched.length) return;
		// Looked for only once something matched, since it reads the layout.
		const modal = blockingModal();
		const found = matched.filter(({ el }) => !modal || modal.contains(el));
		if (!found.length) return;

		// The longest match wins, so B on its own and G then B both stay
		// reachable: G then B runs the sequence, B alone runs the key. Between
		// two of one length, the first in the document has them.
		const { el } = found.sort(
			(a, b) =>
				b.steps.length - a.steps.length ||
				(a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1),
		)[0];
		event.preventDefault();
		pressed = [];
		const proceed = el.dispatchEvent(new CustomEvent("hue:shortcut", { cancelable: true }));
		if (proceed) el.click();
	});
}
