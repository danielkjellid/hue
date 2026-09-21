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
