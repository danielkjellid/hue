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
	Alpine.data("hueCommand", (startsOpen, emptyMessage) => {
		// The items as they are shown, worked out by filter(), the only thing
		// that changes them. Kept out of the component's state, which would
		// wrap each element in a proxy.
		let ordered = [];

		return {
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
				this.filter();
				this.$watch("open", (open) => (open ? this.opened() : null));
				if (this.open) this.opened();
			},

			close() {
				this.open = false;
			},

			all() {
				return [...this.$refs.listbox.querySelectorAll('[role="option"]')];
			},

			// In the order they are shown. Read on every key press, so it is the
			// list filter() worked out rather than something sorted again here.
			options() {
				return ordered;
			},

			opened() {
				this.query = "";
				this.filter();
				// The search field carries autofocus rather than being focused
				// here, so the focus trap moves focus into it and remembers the
				// control that opened the palette to give focus back to.
				this.$nextTick(() => this.activate(this.enabled()[0]));
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
				// By group, then by rank, then as the server drew them, which a
				// stable sort keeps. A group's place is where it first appears; an
				// item outside any group is a place of its own.
				const groups = new Map();
				const shown = [];
				for (const item of this.all()) {
					const label = item.dataset.label.toLowerCase();
					const words = `${label} ${item.dataset.keywords ?? ""}`.toLowerCase();
					let rank = 0;
					if (query && !label.startsWith(query)) {
						if (words.split(/\s+/).some((word) => word.startsWith(query)))
							rank = 1;
						else if (words.includes(query)) rank = 2;
						else rank = -1;
					}
					item.hidden = rank === -1;
					item.style.order = rank > 0 ? String(rank) : "";
					if (rank === -1) continue;
					const group = item.closest('[role="group"]') ?? item;
					if (!groups.has(group)) groups.set(group, groups.size);
					shown.push({ item, rank, group: groups.get(group) });
				}
				ordered = shown
					.sort((a, b) => a.group - b.group || a.rank - b.rank)
					.map(({ item }) => item);
				for (const group of this.$refs.listbox.querySelectorAll(
					'[role="group"]',
				)) {
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
				if (item.tagName !== "A")
					item.dispatchEvent(new CustomEvent("command"));
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
				}
			},
		};
	});
}
