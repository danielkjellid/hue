/**
 * hueSelect: the ARIA select-only combobox.
 *
 * Focus never leaves the trigger. The option the keys are on is named by
 * aria-activedescendant instead, which is what lets a screen reader follow
 * the arrows through a list it cannot focus. The options are read from the
 * listbox each time rather than kept in a list here, so the server can draw
 * whatever options it likes and nothing has to be kept in step.
 */

// How long a pause ends a typed word: "ca" finds Canada, "c" then "a" a
// second later finds the next option starting with a.
const TYPEAHEAD_MS = 500;
const PAGE = 10;

export function registerSelectData(Alpine) {
	Alpine.data("hueSelect", (value, placeholder) => ({
		open: false,
		value,
		placeholder,
		active: null,
		typed: "",
		typedAt: 0,

		get label() {
			return this.selected()?.dataset.label ?? "";
		},

		options() {
			return [...this.$refs.listbox.querySelectorAll('[role="option"]')];
		},

		enabled() {
			return this.options().filter(
				(option) => option.getAttribute("aria-disabled") !== "true",
			);
		},

		selected() {
			return this.options().find((option) => option.dataset.value === this.value);
		},

		show(which = "selected") {
			if (this.open) return;
			// At least as wide as the trigger, so the list reads as belonging
			// to it; wider when an option needs the room.
			this.$refs.listbox.style.minWidth = `${this.$refs.trigger.offsetWidth}px`;
			this.open = true;
			const enabled = this.enabled();
			const start =
				which === "first"
					? enabled[0]
					: which === "last"
						? enabled.at(-1)
						: (this.selected() ?? enabled[0]);
			this.$nextTick(() => this.activate(start));
		},

		hide() {
			this.open = false;
			this.active = null;
		},

		activate(option) {
			if (!option || option.getAttribute("aria-disabled") === "true") return;
			this.active = option.id;
			option.scrollIntoView({ block: "nearest" });
		},

		// Stops at either end rather than wrapping, as the pattern asks: a
		// list that wraps gives no sign of having reached its last option.
		move(step) {
			const enabled = this.enabled();
			const at = enabled.findIndex((option) => option.id === this.active);
			const next = Math.min(Math.max(at + step, 0), enabled.length - 1);
			this.activate(enabled[at === -1 ? 0 : next]);
		},

		choose(option) {
			if (!option || option.getAttribute("aria-disabled") === "true") return;
			this.commit(option);
			this.hide();
			this.$refs.trigger.focus();
		},

		commit(option) {
			if (option.dataset.value === this.value) return;
			this.value = option.dataset.value;
			// Set now rather than on the next render, so anything listening
			// for the change reads the new value.
			const input = this.$refs.input;
			input.value = this.value;
			input.dispatchEvent(new Event("input", { bubbles: true }));
			input.dispatchEvent(new Event("change", { bubbles: true }));
		},

		current() {
			return this.options().find((option) => option.id === this.active);
		},

		// Typing moves to the next option that starts with what was typed.
		// Typing one letter again cycles through the options starting with it.
		typeahead(char) {
			const now = Date.now();
			this.typed = now - this.typedAt > TYPEAHEAD_MS ? char : this.typed + char;
			this.typedAt = now;
			const repeated = [...this.typed].every((c) => c === this.typed[0]);
			const search = repeated ? this.typed[0] : this.typed;

			const enabled = this.enabled();
			const at = enabled.findIndex((option) => option.id === this.active);
			// A new word may match the option already active; a repeated
			// letter means the one after it.
			const offset = repeated || this.typed.length === 1 ? 1 : 0;
			const ordered = [
				...enabled.slice(at + offset),
				...enabled.slice(0, at + offset),
			];
			const found = ordered.find((option) =>
				option.dataset.label.toLowerCase().startsWith(search.toLowerCase()),
			);
			if (found) this.activate(found);
		},

		key(event) {
			const { key, altKey, ctrlKey, metaKey } = event;
			const printable = key.length === 1 && key !== " " && !ctrlKey && !metaKey;

			if (!this.open) {
				const opens = {
					ArrowDown: "selected",
					ArrowUp: "selected",
					Enter: "selected",
					" ": "selected",
					Home: "first",
					End: "last",
				};
				if (key in opens) {
					event.preventDefault();
					this.show(opens[key]);
				} else if (printable) {
					this.show();
					this.$nextTick(() => this.typeahead(key));
				}
				return;
			}

			if (key === "ArrowUp" && altKey) {
				event.preventDefault();
				this.choose(this.current());
			} else if (key === "ArrowDown") {
				event.preventDefault();
				this.move(1);
			} else if (key === "ArrowUp") {
				event.preventDefault();
				this.move(-1);
			} else if (key === "Home") {
				event.preventDefault();
				this.activate(this.enabled()[0]);
			} else if (key === "End") {
				event.preventDefault();
				this.activate(this.enabled().at(-1));
			} else if (key === "PageDown") {
				event.preventDefault();
				this.move(PAGE);
			} else if (key === "PageUp") {
				event.preventDefault();
				this.move(-PAGE);
			} else if (key === "Enter" || key === " ") {
				event.preventDefault();
				// A space while typing a word is part of the word.
				if (key === " " && Date.now() - this.typedAt < TYPEAHEAD_MS) {
					this.typeahead(key);
				} else {
					this.choose(this.current());
				}
			} else if (key === "Escape") {
				// Closing the list is all Escape does here, so a dialog the
				// select sits in stays open.
				event.preventDefault();
				event.stopPropagation();
				this.hide();
			} else if (key === "Tab") {
				// Tab keeps its default and moves on, taking the active option
				// with it.
				const option = this.current();
				if (option) this.commit(option);
				this.hide();
			} else if (printable) {
				this.typeahead(key);
			}
		},
	}));
}
