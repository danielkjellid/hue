/**
 * hueTableSelection: which rows are ticked.
 *
 * The row checkboxes are real checkboxes carrying a name and a value, so a
 * form around the table posts the selection without any of this. What needs
 * watching is the one in the header, which has a third state - some rows,
 * not all - that no attribute can express and only a DOM property can set.
 */
export function registerTableData(Alpine) {
	Alpine.data("hueTableSelection", (values = []) => ({
		values,
		selected: [],

		get all() {
			return this.values.length > 0 && this.selected.length === this.values.length;
		},

		get some() {
			return this.selected.length > 0 && !this.all;
		},

		toggleAll(checked) {
			this.selected = checked ? [...this.values] : [];
		},

		isSelected(value) {
			return this.selected.includes(value);
		},
	}));
}

/**
 * hueTableSearch: the keyboard around the box above a table.
 *
 * The box itself is a plain GET form that submits itself after a pause, so
 * none of this is needed for it to work. What is here is the two keys the
 * pattern promises: slash to get to it from anywhere on the page, and
 * escape to empty it without reaching for the mouse.
 */
export function registerTableSearch(Alpine) {
	Alpine.data("hueTableSearch", () => ({
		focusField(event) {
			// Ignored while focus is in a field, or slash would be
			// untypeable everywhere else on the page.
			const target = event.target;
			const tag = (target.tagName || "").toLowerCase();
			if (
				tag === "input" ||
				tag === "textarea" ||
				tag === "select" ||
				target.isContentEditable
			) {
				return;
			}
			event.preventDefault();
			this.$refs.field.focus();
			this.$refs.field.select();
		},

		clearField(event) {
			// An empty box has nothing to clear, so escape goes on to
			// whatever else is listening - a dialog the table is inside.
			if (!this.$refs.field.value) {
				return;
			}
			event.stopPropagation();
			this.$refs.field.value = "";
			this.$refs.field.form.requestSubmit();
		},
	}));
}

/**
 * hueTableFilters: what is on, read off the controls that say so.
 *
 * The panel behind the Filter button is a plain GET form, so the server
 * already knows what is on: it rendered the boxes ticked. What this adds
 * is the count on the trigger and the chips under it, which are the same
 * fact stated twice on purpose - a filter that only exists behind a
 * closed popover gets blamed on the data.
 *
 * Derived from the form rather than sent down beside it, so a tick and
 * the chip it puts up happen in the same frame instead of a round trip
 * apart.
 */
export function registerTableFilters(Alpine) {
	Alpine.data("hueTableFilters", () => ({
		applied: [],

		init() {
			this.read();
		},

		controls() {
			return Array.from(this.$refs.form.querySelectorAll("[data-filter]"));
		},

		read() {
			this.applied = this.controls()
				.filter((el) => (el.type === "checkbox" ? el.checked : el.value))
				.map((el) => ({
					group: el.dataset.filter,
					name: el.dataset.group || el.dataset.filter,
					value: el.type === "checkbox" ? el.value : "",
					label: el.dataset.option || el.value,
				}));
		},

		clearControl(el) {
			if (el.type === "checkbox") {
				el.checked = false;
			} else {
				el.value = "";
			}
		},

		remove(chip) {
			for (const el of this.controls()) {
				if (el.dataset.filter !== chip.group) continue;
				if (el.type === "checkbox" && el.value !== chip.value) continue;
				this.clearControl(el);
			}
			this.apply();
		},

		clear() {
			for (const el of this.controls()) {
				this.clearControl(el);
			}
			this.apply();
		},

		apply() {
			this.read();
			this.$refs.form.requestSubmit();
		},
	}));
}
