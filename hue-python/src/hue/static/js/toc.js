/**
 * hueToc: which heading in a table of contents the reader has got to.
 *
 * The rail and every distance along it are worked out by the server, so all
 * this does is move an index. It reads positions rather than observing
 * intersections because what it wants is the last heading to have reached
 * the top of the screen - one comparison per heading, and no edge cases
 * about how much of a section happens to be in view.
 */

// How far past its own line a heading may be and still count as reached.
// Enough to absorb the rounding in a scroll position, and no more.
const SLACK = 8;

/**
 * Where a heading sits relative to the line it is reached at.
 *
 * That line is the top of the viewport, less the scroll-margin the page
 * keeps clear for whatever it holds up there - which is to say, exactly
 * where clicking the entry would put the heading. Measuring from anywhere
 * further down the screen makes a short section unreachable: click its
 * entry, and the next heading would already have crossed the line.
 */
function distanceToLine(element) {
	const margin = parseFloat(getComputedStyle(element).scrollMarginTop) || 0;
	return element.getBoundingClientRect().top - margin;
}

function activeIndex(ids, fallback) {
	const present = [];
	for (let index = 0; index < ids.length; index++) {
		const element = document.getElementById(ids[index]);
		if (element) present.push({ index, element });
	}

	// A list whose headings are not on this page: a specimen in a gallery, a
	// fragment rendered on its own. Leave it saying what it was given.
	if (present.length === 0) return fallback;

	// The last section is often too short to fill the screen, so the page
	// stops scrolling before its heading ever reaches the line. Once it can
	// go no further, that heading is what is being looked at.
	const bottom = window.innerHeight + window.scrollY;
	if (bottom >= document.documentElement.scrollHeight - 2) {
		return present[present.length - 1].index;
	}

	// The first heading stands for everything above it, including the part
	// of the page that comes before the first one.
	let active = present[0].index;
	for (const { index, element } of present) {
		if (distanceToLine(element) <= SLACK) active = index;
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
