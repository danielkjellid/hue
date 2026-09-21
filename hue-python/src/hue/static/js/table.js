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
			// A page-wide key can only belong to one thing. With two
			// tables on the page there is no answer to which one slash
			// means, so it means neither and stays a slash.
			if (document.querySelectorAll("[data-hue-table-search]").length > 1) {
				return;
			}
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

		dropEmpty() {
			// A disabled control is not submitted, so an empty field
			// leaves no trace in a URL somebody is meant to be able to
			// send on. Re-enabled straight after, because the form is
			// still on the page and still the one being typed into.
			const empty = this.controls().filter(
				(el) => el.type !== "checkbox" && !el.value,
			);
			for (const el of empty) {
				el.disabled = true;
			}
			queueMicrotask(() => {
				for (const el of empty) {
					el.disabled = false;
				}
			});
		},
	}));
}

/**
 * hueTableColumns: which columns are put away.
 *
 * A box that is ticked is a column that is showing, which is the way
 * round anybody reads a list of columns - but what the URL carries is
 * the ones that are hidden, so that adding a column later shows it to
 * somebody following an old link rather than hiding it from them.
 *
 * A checkbox can only submit itself when it is ticked, so the two cannot
 * be the same control: the boxes are for reading and one hidden field
 * carries the answer.
 */
export function registerTableColumns(Alpine) {
	Alpine.data("hueTableColumns", (hidden = []) => ({
		hidden,

		showing(key) {
			return !this.hidden.includes(key);
		},

		toggle(key, shown) {
			this.hidden = shown
				? this.hidden.filter((other) => other !== key)
				: [...this.hidden, key];
			this.$refs.form.requestSubmit();
		},
	}));
}
