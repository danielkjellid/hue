/**
 * hueTableSelection: which rows are ticked.
 *
 * The row checkboxes are real checkboxes carrying a name and a value, so the
 * table's form posts the selection without any of this. What needs watching
 * is the checkbox in the header, which has a third state (some rows, not
 * all) that no attribute can express and only a DOM property can set.
 *
 * The values are read off the rows on the page each time rather than handed
 * in once, because a sort, a page or a search replaces the rows without
 * replacing this scope.
 *
 * There is one selection per page. Each table's bar floats in the same spot,
 * so starting a selection in one table clears it in every other. Otherwise
 * one bar would cover another while its rows stayed ticked, and Escape would
 * clear both.
 */
export function registerTableSelection(Alpine) {
	Alpine.data("hueTableSelection", () => ({
		// Declared, so Alpine keeps them on this scope instead of writing
		// them to the outermost one on the page.
		frame: null,
		onOtherSelection: null,
		selected: [],

		init() {
			this.frame = this.$el;
			this.onOtherSelection = (event) => {
				if (event.detail !== this.frame && this.selected.length) {
					this.selected = [];
				}
			};
			window.addEventListener("hue-table-selection", this.onOtherSelection);
			this.$watch("selected", (now, before) => {
				if (now.length && !before?.length) {
					window.dispatchEvent(
						new CustomEvent("hue-table-selection", { detail: this.frame }),
					);
				}
			});
		},

		destroy() {
			window.removeEventListener("hue-table-selection", this.onOtherSelection);
		},

		get values() {
			if (!this.frame) {
				return [];
			}
			return Array.from(
				this.frame.querySelectorAll("[data-hue-row-select]"),
				(box) => box.value,
			);
		},

		get all() {
			return this.values.length > 0 && this.selected.length === this.values.length;
		},

		get some() {
			return this.selected.length > 0 && !this.all;
		},

		toggleAll(checked) {
			this.selected = checked ? [...this.values] : [];
		},

		clear() {
			this.selected = [];
		},

		// Drops what is no longer on the page, so a bulk action can only
		// reach rows the reader can see.
		prune() {
			const showing = this.values;
			this.selected = this.selected.filter((value) => showing.includes(value));
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
	Alpine.data("hueTableFilters", (table = "") => ({
		table,
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
					filter: el.dataset.filter,
					filterLabel: el.dataset.filterLabel || el.dataset.filter,
					value: el.type === "checkbox" ? el.value : "",
					label: el.dataset.option || el.value,
				}));
			narrowed(this.table, { filters: this.applied.length });
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
				if (el.dataset.filter !== chip.filter) continue;
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
	Alpine.data("hueTableColumns", (hidden = [], table = "") => ({
		table,
		hidden,

		showing(key) {
			return !this.hidden.includes(key);
		},

		toggle(key, shown) {
			this.hidden = shown
				? this.hidden.filter((other) => other !== key)
				: [...this.hidden, key];
			narrowed(this.table, { hidden: this.hidden.length });
			this.$refs.form.requestSubmit();
		},
	}));
}

/**
 * Says how narrowed a table is, for whatever is listening for that table.
 *
 * The filter and column panels live in the toolbar, which a response leaves
 * alone, so nothing else redraws the reset button when either changes.
 */
function narrowed(table, counts) {
	window.dispatchEvent(
		new CustomEvent("hue-table-narrowed", { detail: { table, ...counts } }),
	);
}

/**
 * hueTableReset: shown while a table is filtered or has columns hidden.
 *
 * Starts from the counts the server rendered, and hears about changes from
 * the panels, matched by the table's key so two tables on a page keep their
 * own.
 */
export function registerTableReset(Alpine) {
	Alpine.data("hueTableReset", (table = "", filters = 0, hidden = 0) => ({
		table,
		filters,
		hidden,

		get narrowed() {
			return this.filters > 0 || this.hidden > 0;
		},

		hear(detail) {
			if (detail.table !== this.table) {
				return;
			}
			if ("filters" in detail) {
				this.filters = detail.filters;
			}
			if ("hidden" in detail) {
				this.hidden = detail.hidden;
			}
		},
	}));
}
