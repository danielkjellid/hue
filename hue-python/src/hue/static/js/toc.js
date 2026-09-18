/**
 * hueToc: which heading in a table of contents the reader has got to.
 *
 * The rail and every distance along it are worked out by the server, so all
 * this does is move an index. It reads positions rather than observing
 * intersections because what it wants is the last heading above the reading
 * line - one comparison per heading, and no edge cases about how much of a
 * section happens to be in view.
 */

// Where down the screen the reader is taken to be reading, as a fraction of
// the viewport. Not the very top: a heading scrolled to sits under whatever
// the page keeps up there.
const LINE = 0.3;

function activeIndex(ids, fallback) {
	const present = [];
	for (let index = 0; index < ids.length; index++) {
		const element = document.getElementById(ids[index]);
		if (element) present.push({ index, element });
	}

	// A list whose headings are not on this page: a specimen in a gallery, a
	// fragment rendered on its own. Leave it saying what it was given.
	if (present.length === 0) return fallback;

	// The last section is often too short to ever reach the line. Once the
	// page can go no further, it is what is being looked at.
	const bottom = window.innerHeight + window.scrollY;
	if (bottom >= document.documentElement.scrollHeight - 2) {
		return present[present.length - 1].index;
	}

	const line = window.innerHeight * LINE;
	let active = present[0].index;
	for (const { index, element } of present) {
		if (element.getBoundingClientRect().top <= line) active = index;
	}
	return active;
}

export function registerTocData(Alpine) {
	Alpine.data("hueToc", (ids, current, reach) => ({
		ids,
		reach,
		active: current,
		// The path ends at the last heading, so the distance to it is the
		// whole of it - the fill and the dot are both fractions of this.
		length: reach.length ? reach[reach.length - 1] : 0,

		get at() {
			return this.length ? (this.reach[this.active] / this.length) * 100 : 0;
		},

		init() {
			let pending = false;
			const read = () => {
				pending = false;
				this.active = activeIndex(this.ids, current);
			};
			this.onMove = () => {
				if (pending) return;
				pending = true;
				requestAnimationFrame(read);
			};
			// Capturing, so a page that scrolls inside a container rather than
			// the window is heard too. Scroll events do not bubble.
			document.addEventListener("scroll", this.onMove, true);
			window.addEventListener("resize", this.onMove);
			read();
		},

		destroy() {
			document.removeEventListener("scroll", this.onMove, true);
			window.removeEventListener("resize", this.onMove);
		},
	}));
}
