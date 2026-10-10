/**
 * hueCommand: a command palette.
 *
 * A modal whose search field keeps focus while the arrow keys move a marker
 * through the items by aria-activedescendant. Typing hides the items that do
 * not match and moves those that start with what was typed to the top of
 * their group, since the first result is the one Enter runs.
 */

import { listbox } from "./listbox.js";

// Counted here rather than given by the server, which would have to keep two
// palettes on a page from sharing ids.
let palettes = 0;

export function registerCommandData(Alpine) {
	Alpine.data("hueCommand", (startsOpen, emptyMessage) => ({
		...listbox,
		open: startsOpen,
		emptyMessage,
		query: "",
		active: null,
		empty: false,

		init() {
			const list = `hue-command-${++palettes}`;
			this.$refs.listbox.id = list;
			this.$refs.input.setAttribute("aria-controls", list);
			this.all().forEach((item, index) => {
				if (!item.id) item.id = `${list}-${index}`;
			});
			this.$watch("open", (open) => (open ? this.opened() : null));
			if (this.open) this.opened();
		},

		close() {
			this.open = false;
		},

		all() {
			return [...this.$refs.listbox.querySelectorAll('[role="option"]')];
		},

		// In the order they are shown, which the ranking can change within
		// a group: by group, then by rank, then as the server drew them.
		options() {
			const top = (item) =>
				[...this.$refs.listbox.children].findIndex((child) => child.contains(item));
			return this.all()
				.filter((item) => !item.hidden)
				.sort(
					(a, b) => top(a) - top(b) || (+a.style.order || 0) - (+b.style.order || 0),
				);
		},

		opened() {
			this.query = "";
			this.filter();
			this.$nextTick(() => {
				this.$refs.input.focus();
				this.activate(this.enabled()[0]);
			});
		},

		search() {
			this.filter();
			this.$nextTick(() => this.activate(this.enabled()[0]));
		},

		// An item stays when its label or a keyword contains what was typed.
		// One whose label starts with it ranks first, then one with a word
		// that does, then the rest.
		filter() {
			const query = this.query.trim().toLowerCase();
			for (const item of this.all()) {
				const label = item.dataset.label.toLowerCase();
				const words = `${label} ${item.dataset.keywords ?? ""}`.toLowerCase();
				let rank = 0;
				if (query && !label.startsWith(query)) {
					if (words.split(/\s+/).some((word) => word.startsWith(query))) rank = 1;
					else if (words.includes(query)) rank = 2;
					else rank = -1;
				}
				item.hidden = rank === -1;
				item.style.order = rank > 0 ? String(rank) : "";
			}
			for (const group of this.$refs.listbox.querySelectorAll('[role="group"]')) {
				group.hidden = !group.querySelector('[role="option"]:not([hidden])');
			}
			this.empty = this.options().length === 0;
			if (!this.current()) this.active = null;
		},

		run(item, event) {
			if (item.getAttribute("aria-disabled") === "true") {
				event?.preventDefault();
				return;
			}
			this.close();
			// A link goes where it points by itself; an action is reached
			// through the event its item listens for.
			if (item.tagName !== "A") item.dispatchEvent(new CustomEvent("command"));
		},

		key(event) {
			const { key } = event;
			if (key === "ArrowDown") {
				event.preventDefault();
				this.move(1);
			} else if (key === "ArrowUp") {
				event.preventDefault();
				this.move(-1);
			} else if (key === "Home" && event.ctrlKey) {
				event.preventDefault();
				this.activate(this.enabled()[0]);
			} else if (key === "End" && event.ctrlKey) {
				event.preventDefault();
				this.activate(this.enabled().at(-1));
			} else if (key === "Enter") {
				event.preventDefault();
				// Clicked rather than run, so a link is followed the way a
				// click on it would follow it.
				this.current()?.click();
			} else if (key === "Escape" && this.query) {
				// The first Escape takes back what was typed, the second
				// closes, so a wrong search costs one key rather than the
				// palette.
				event.preventDefault();
				event.stopPropagation();
				this.query = "";
				this.search();
			} else if (key === "Escape") {
				event.preventDefault();
				this.close();
			}
		},
	}));
}
