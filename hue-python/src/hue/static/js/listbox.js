/**
 * Moving through a listbox by aria-activedescendant, shared by hueSelect and
 * hueCombobox.
 *
 * The options are read from the listbox on every call rather than kept in a
 * list, so the server can draw whatever options it likes. An option that is
 * hidden, because a combobox filtered it out, is not there to move to.
 */
export const listbox = {
	options() {
		return [...this.$refs.listbox.querySelectorAll('[role="option"]')].filter(
			(option) => !option.hidden,
		);
	},

	enabled() {
		return this.options().filter(
			(option) => option.getAttribute("aria-disabled") !== "true",
		);
	},

	current() {
		return this.options().find((option) => option.id === this.active);
	},

	activate(option) {
		if (!option || option.getAttribute("aria-disabled") === "true") return;
		this.active = option.id;
		option.scrollIntoView({ block: "nearest" });
	},

	// Stops at either end rather than wrapping, as the pattern asks: a list
	// that wraps gives no sign of having reached its last option.
	move(step) {
		const enabled = this.enabled();
		const at = enabled.findIndex((option) => option.id === this.active);
		const next = Math.min(Math.max(at + step, 0), enabled.length - 1);
		this.activate(enabled[at === -1 ? 0 : next]);
	},
};
