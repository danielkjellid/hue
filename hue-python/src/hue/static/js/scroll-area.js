/**
 * hueScrollArea: whether there is more content above and below.
 *
 * Only the faded variant uses it. The two ends are tracked separately so
 * each edge softens when there is something that way to continue into, and
 * stays sharp when there is not - a fade at the top of a list that is
 * already at the top dims its first line for nothing.
 */
export function registerScrollAreaData(Alpine) {
	Alpine.data("hueScrollArea", () => ({
		above: false,
		below: false,
		// Declared rather than assigned in init(): Alpine writes a property
		// its data object never mentioned to the outermost scope on the page
		// instead of to this component, and the next scroll area would then
		// disconnect this one's observer as its own.
		sizes: null,

		init() {
			this.edges();
			// Content arriving after the first paint - a fragment filling a
			// list, an image finishing - changes which edges there are, and
			// nothing scrolls to say so.
			this.sizes = new ResizeObserver(() => this.edges());
			this.sizes.observe(this.$el);
			for (const child of this.$el.children) this.sizes.observe(child);
		},

		destroy() {
			this.sizes?.disconnect();
		},

		edges() {
			const { scrollTop, clientHeight, scrollHeight } = this.$el;
			this.above = scrollTop > 1;
			// A pixel of slack: a fractional scroll height is normal at odd
			// zoom levels, and without it the bottom edge never resolves.
			this.below = scrollTop + clientHeight < scrollHeight - 1;
		},
	}));
}
