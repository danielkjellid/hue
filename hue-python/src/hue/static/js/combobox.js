/**
 * hueCombobox: the ARIA combobox with list autocomplete.
 *
 * The text field keeps focus throughout. Typing filters the options by
 * hiding the ones whose label does not contain what was typed, and the
 * arrows move through what is left by aria-activedescendant.
 *
 * selected holds what is chosen as value and label pairs rather than as
 * values alone, because the label has to be shown in the field or on a
 * token even when its option has been filtered out.
 */

import { listbox } from "./listbox.js";

export function registerComboboxData(Alpine) {
	Alpine.data("hueCombobox", (selected, multiple, emptyMessage) => ({
		...listbox,
		open: false,
		active: null,
		selected,
		multiple,
		emptyMessage,
		// Whether the list is narrowed to what was typed. A single combobox
		// opened by the arrow keys shows its chosen label in the field, and
		// that should not filter the list down to the one option.
		filtering: false,
		empty: false,
		returning: false,
		query: multiple ? "" : (selected[0]?.label ?? ""),
		// What x-modelable hands a parent's x-model: the value, or for a
		// multiple combobox the list of values.
		value: selected[0]?.value ?? "",
		values: selected.map((item) => item.value),

		init() {
			// A parent changing the bound value arrives here.
			this.$watch("value", (value) => {
				if (!this.multiple && value !== (this.selected[0]?.value ?? "")) {
					this.adopt(value ? [value] : []);
				}
			});
			this.$watch("values", (values) => {
				if (this.multiple && values.join("\n") !== this.valuesKey()) {
					this.adopt(values);
				}
			});
		},

		valuesKey() {
			return this.selected.map((item) => item.value).join("\n");
		},

		labelOf(value) {
			const option = [
				...this.$refs.listbox.querySelectorAll('[role="option"]'),
			].find((option) => option.dataset.value === value);
			return option?.dataset.label ?? value;
		},

		adopt(values) {
			this.selected = values.map((value) => ({
				value,
				label: this.labelOf(value),
			}));
			if (!this.multiple) this.query = this.selected[0]?.label ?? "";
		},

		chosen(value) {
			return this.selected.some((item) => item.value === value);
		},

		show(which = "selected") {
			if (this.open) return;
			// At least as wide as the field, so the list reads as belonging
			// to it; wider when an option needs the room.
			this.$refs.popup.style.minWidth = `${this.$refs.shell.offsetWidth}px`;
			this.open = true;
			this.filter();
			if (which === "none") return;
			this.$nextTick(() => {
				const enabled = this.enabled();
				const chosen = enabled.find((option) => this.chosen(option.dataset.value));
				this.activate(which === "last" ? enabled.at(-1) : (chosen ?? enabled[0]));
			});
		},

		hide() {
			this.open = false;
			this.active = null;
			this.filtering = false;
			this.query = this.multiple ? "" : (this.selected[0]?.label ?? "");
			this.filter();
		},

		toggle() {
			if (this.open) {
				this.hide();
			} else {
				this.show();
				this.$refs.input.focus();
			}
		},

		search() {
			this.filtering = true;
			if (!this.open) this.show("none");
			else this.filter();
			// The first match is where Enter goes, so a word and Enter picks it.
			// filter() has just cleared the active option, so waiting a tick
			// would leave an Enter that arrives in between with nothing to pick.
			this.activate(this.enabled()[0]);
		},

		filter() {
			const query = this.filtering ? this.query.trim().toLowerCase() : "";
			const all = this.$refs.listbox.querySelectorAll('[role="option"]');
			for (const option of all) {
				option.hidden =
					query !== "" && !option.dataset.label.toLowerCase().includes(query);
			}
			for (const group of this.$refs.listbox.querySelectorAll('[role="group"]')) {
				group.hidden = !group.querySelector('[role="option"]:not([hidden])');
			}
			this.empty = this.options().length === 0;
			if (!this.current()) this.active = null;
		},

		choose(option) {
			if (!option || option.getAttribute("aria-disabled") === "true") return;
			const item = { value: option.dataset.value, label: option.dataset.label };
			if (this.multiple) {
				// Toggled, and the list stays open for the next one.
				this.selected = this.chosen(item.value)
					? this.selected.filter((each) => each.value !== item.value)
					: [...this.selected, item];
				this.query = "";
				this.filtering = false;
				this.filter();
				this.activate(option);
			} else {
				this.selected = [item];
				this.hide();
			}
			this.changed();
		},

		remove(value) {
			this.selected = this.selected.filter((item) => item.value !== value);
			// The button that was pressed is gone, and focus with it. Moved to
			// the field without opening the list, which removing a token did
			// not ask for.
			if (document.activeElement !== this.$refs.input) {
				this.returning = true;
				this.$refs.input.focus();
			}
			this.changed();
		},

		// The list opens as the field gets focus, so every option is in view
		// before anything is typed.
		focused() {
			if (this.returning) this.returning = false;
			else this.show();
		},

		changed() {
			this.value = this.selected[0]?.value ?? "";
			this.values = this.selected.map((item) => item.value);
			// After the submitted fields are redrawn, so a listener reads
			// the new value from the form.
			this.$nextTick(() =>
				this.$refs.input.dispatchEvent(new Event("change", { bubbles: true })),
			);
		},

		// Focus moving somewhere outside the combobox closes it. A single
		// combobox whose text was cleared is cleared, which is how its value
		// is taken away.
		leave(event) {
			if (this.$root.contains(event.relatedTarget)) return;
			if (!this.multiple && this.query.trim() === "" && this.selected.length) {
				this.selected = [];
				this.changed();
			}
			this.hide();
		},

		key(event) {
			const { key, altKey } = event;
			if (key === "ArrowDown") {
				event.preventDefault();
				if (!this.open) this.show(altKey ? "none" : "selected");
				else this.move(1);
			} else if (key === "ArrowUp") {
				event.preventDefault();
				if (!this.open) this.show("last");
				else if (altKey) this.hide();
				else this.move(-1);
			} else if (key === "Enter") {
				// Closed, Enter is left to submit the form the field is in.
				if (this.open && this.current()) {
					event.preventDefault();
					this.choose(this.current());
				}
			} else if (key === "Escape") {
				if (this.open) {
					// Only the list closes, not a dialog the field sits in.
					event.preventDefault();
					event.stopPropagation();
					this.hide();
				}
			} else if (key === "Backspace") {
				if (this.multiple && this.query === "" && this.selected.length) {
					this.remove(this.selected.at(-1).value);
				}
			}
		},
	}));
}
