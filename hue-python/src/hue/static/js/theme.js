/**
 * The colour theme store.
 *
 * Three states, not two: "system" has to be a real, selectable option, because
 * a binary toggle cannot represent "follow my OS". The stored value is always
 * the *choice*; `data-theme` on <html> only ever carries the resolved
 * light/dark, which is what the CSS matches on.
 *
 * The first application happens in a blocking <head> script rendered by
 * BasePage, before first paint. This store takes over from there and keeps the
 * two in sync, so it must resolve the same way.
 */

const CHOICES = ["light", "dark", "system"];

function prefersDark() {
	return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function read(key) {
	try {
		const stored = localStorage.getItem(key);
		return CHOICES.includes(stored) ? stored : null;
	} catch {
		// Private modes and blocked site data throw rather than return null.
		return null;
	}
}

function write(key, choice) {
	try {
		localStorage.setItem(key, choice);
	} catch {
		// Not being able to remember the choice is survivable; failing is not.
	}
}

export function registerThemeStore(Alpine, storageKey) {
	Alpine.store("theme", {
		choice: read(storageKey) ?? "system",

		init() {
			this.apply();
			// Follow the OS while, and only while, the user is on "system".
			window
				.matchMedia("(prefers-color-scheme: dark)")
				.addEventListener("change", () => {
					if (this.choice === "system") this.apply();
				});
		},

		/** The light/dark actually on screen, with "system" resolved. */
		get resolved() {
			if (this.choice === "system") return prefersDark() ? "dark" : "light";
			return this.choice;
		},

		select(choice) {
			if (!CHOICES.includes(choice)) return;
			this.choice = choice;
			write(storageKey, choice);
			this.apply();
		},

		apply() {
			document.documentElement.setAttribute("data-theme", this.resolved);
		},
	});
}
