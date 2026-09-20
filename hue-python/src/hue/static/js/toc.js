/**
 * hueToc: the headings on the page, and which one the reader has got to.
 *
 * Everything here is measured rather than assumed. The entries come from
 * the document, their nesting from the heading levels, and the rail from
 * where the rows actually landed - so a heading long enough to wrap keeps
 * its node beside the line the eye starts on, and nothing has to be kept in
 * step with the page by hand.
 */

const RAIL_X = 5; // the dot needs room to its left; an SVG clips at its edge
const INDENT = 16; // what one level of nesting moves, rail and label alike
const GAP = 18; // rail to the first letter
const BEND = 24; // the vertical span a change of level curves over
const STROKE = 1.5;
const DOT = 4;
const TERMINAL = 3;

// How far past its own line a heading may be and still count as reached.
// Enough to absorb the rounding in a scroll position, and no more.
const SLACK = 8;

/**
 * An id for a heading that has none, from the words in it.
 *
 * Assigned rather than required, so a page can be written as plain headings
 * and still be linkable. taken carries every id already on the page, this
 * component's own included, so two sections called the same thing get two
 * different links.
 */
function slugify(text, taken) {
	const base =
		text
			.trim()
			.toLowerCase()
			.replace(/[^\p{L}\p{N}\s-]/gu, "")
			.replace(/\s+/g, "-")
			.replace(/^-+|-+$/g, "") || "section";

	let id = base;
	let suffix = 2;
	while (taken.has(id)) id = `${base}-${suffix++}`;
	taken.add(id);
	return id;
}

/**
 * What an entry is called.
 *
 * The heading's own words, unless it says otherwise: data-toc on the
 * heading renames it in the contents without renaming it on the page,
 * which is what a heading too long for a list down a side needs. It sits on
 * the heading rather than in a list somewhere else, so there is still only
 * one place to change when the section changes.
 */
function labelFor(heading) {
	return (heading.dataset.toc || heading.textContent).trim();
}

/**
 * The element an entry links to, and is measured from.
 *
 * The heading's own id where it has one. Failing that, the nearest ancestor
 * that has one and holds no other heading in the list - which is how a
 * <section id> around a plain <h2> links to the section rather than growing
 * a near-duplicate id on the heading inside it. Only when there is neither
 * does the heading get an id of its own.
 */
function anchorFor(heading, headings, taken) {
	if (heading.id) return heading;

	const owner = heading.parentElement?.closest("[id]");
	if (owner && headings.filter((other) => owner.contains(other)).length === 1) {
		return owner;
	}

	heading.id = slugify(heading.textContent, taken);
	return heading;
}

/**
 * How long a cubic is, close enough to put a dot on it.
 *
 * Flattened rather than solved, because the closed form does not exist. The
 * fill and the dot both ride this one number, so they agree with each other
 * whatever it is - and at this size the error is a hundredth of a pixel.
 */
function curveLength(p0, p1, p2, p3, samples = 24) {
	const at = (t) => {
		const u = 1 - t;
		return [
			u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
			u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
		];
	};

	let total = 0;
	let previous = at(0);
	for (let step = 1; step <= samples; step++) {
		const point = at(step / samples);
		total += Math.hypot(point[0] - previous[0], point[1] - previous[1]);
		previous = point;
	}
	return total;
}

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

export function registerTocData(Alpine) {
	Alpine.data("hueToc", ({ of = "main", headings = "h2, h3" } = {}) => ({
		active: 0,
		entries: [],
		reach: [],
		length: 0,

		init() {
			this.build();

			this.onMove = throttle(() => this.read());
			this.onResize = throttle(() => {
				this.draw();
				this.read();
			});
			this.onContent = throttle(() => this.build());

			// Capturing, so a page that scrolls inside a container rather
			// than the window is heard too. Scroll events do not bubble.
			document.addEventListener("scroll", this.onMove, true);
			window.addEventListener("resize", this.onMove);

			// The nav's own width decides where the labels wrap, which is
			// what the rail is drawn from.
			this.sizes = new ResizeObserver(this.onResize);
			this.sizes.observe(this.$root);

			// Content replaced by a fragment is a different set of headings.
			// Attributes are not watched, or setting an id would call this
			// straight back.
			const container = document.querySelector(of);
			if (container) {
				this.content = new MutationObserver(this.onContent);
				this.content.observe(container, { childList: true, subtree: true });
			}

			// Text moves when the real typeface arrives, and every number
			// here came from where the text was.
			document.fonts?.ready.then(() => this.onResize());
		},

		destroy() {
			document.removeEventListener("scroll", this.onMove, true);
			window.removeEventListener("resize", this.onMove);
			this.sizes?.disconnect();
			this.content?.disconnect();
		},

		/**
		 * Read the headings, and lay out a row for each of them.
		 */
		build() {
			const container = document.querySelector(of);
			const found = container ? [...container.querySelectorAll(headings)] : [];
			const levels = found.map((element) => Number(element.tagName.slice(1)));
			// The shallowest level present is the top of the rail, whatever
			// it is: a page of h3s is not a page indented by one.
			const top = Math.min(...levels);
			const taken = new Set(
				[...document.querySelectorAll("[id]")].map((element) => element.id),
			);

			this.entries = found.map((element, index) => ({
				element,
				target: anchorFor(element, found, taken),
				depth: levels[index] - top,
			}));

			// A page with no headings has no contents, and a title over an
			// empty list is worse than nothing at all.
			this.$root.hidden = this.entries.length === 0;

			const list = this.$refs.list;
			list.replaceChildren();
			for (const entry of this.entries) {
				const row = this.$refs.row.content.firstElementChild.cloneNode(true);
				entry.link = row.querySelector("a");
				entry.link.href = `#${entry.target.id}`;
				entry.link.firstElementChild.textContent = labelFor(entry.element);
				entry.link.style.paddingInlineStart = `${RAIL_X + entry.depth * INDENT + GAP}px`;
				list.append(row);
			}

			this.draw();
			this.read();
		},

		/**
		 * Draw the rail from where the rows actually are.
		 *
		 * Straight between two entries at the same level, and an S between
		 * two that are not: a cubic whose control points sit directly below
		 * the one and above the other leaves the curve vertical where it
		 * meets the line, so the joins do not show.
		 */
		draw() {
			if (this.entries.length === 0) return;

			const listTop = this.$refs.list.getBoundingClientRect().top;
			const points = this.entries.map((entry) => ({
				x: RAIL_X + entry.depth * INDENT,
				// The label's first line rather than the row: a heading that
				// wraps still gets its node where the reading starts.
				y: firstLineCentre(entry.link.firstElementChild, listTop),
			}));

			const commands = [`M ${round(points[0].x)} ${round(points[0].y)}`];
			const reach = [0];
			let length = 0;

			for (let index = 1; index < points.length; index++) {
				const a = points[index - 1];
				const b = points[index];
				if (a.x === b.x) {
					commands.push(`L ${round(b.x)} ${round(b.y)}`);
					length += b.y - a.y;
				} else {
					const middle = (a.y + b.y) / 2;
					// Never wider than the gap it has to fit inside, or the
					// curve would lean against the text of either row.
					const bend = Math.min(BEND, b.y - a.y);
					const start = middle - bend / 2;
					const end = middle + bend / 2;
					commands.push(`L ${round(a.x)} ${round(start)}`);
					commands.push(
						`C ${round(a.x)} ${round(middle)} ${round(b.x)} ${round(middle)} ` +
							`${round(b.x)} ${round(end)}`,
					);
					commands.push(`L ${round(b.x)} ${round(b.y)}`);
					length +=
						start - a.y + (b.y - end) +
						curveLength([a.x, start], [a.x, middle], [b.x, middle], [b.x, end]);
				}
				reach.push(length);
			}

			const d = commands.join(" ");
			const last = points[points.length - 1];
			const { rail, track, fill, first, dot } = this.$refs;

			rail.setAttribute("width", round(Math.max(...points.map((p) => p.x)) + DOT + 1));
			rail.setAttribute("height", round(this.$refs.list.offsetHeight));

			for (const path of [track, fill]) {
				path.setAttribute("d", d);
				path.setAttribute("stroke-width", STROKE);
				path.setAttribute("stroke-linecap", "round");
			}
			fill.setAttribute("stroke-dasharray", round(length));

			place(first, points[0], TERMINAL);
			place(this.$refs.last, last, TERMINAL);
			dot.setAttribute("r", DOT);
			dot.style.offsetPath = `path("${d}")`;

			this.reach = reach;
			this.length = length;
			this.apply();
		},

		/**
		 * Work out which heading the reader has got to.
		 */
		read() {
			const entries = this.entries;
			if (entries.length === 0) return;

			// The last section is often too short to fill the screen, so the
			// page stops scrolling before its heading ever reaches the line.
			// Once it can go no further, that heading is what is being
			// looked at.
			const bottom = window.innerHeight + window.scrollY;
			if (bottom >= document.documentElement.scrollHeight - 2) {
				this.select(entries.length - 1);
				return;
			}

			// The first heading stands for everything above it, including
			// whatever comes before it on the page.
			let active = 0;
			entries.forEach((entry, index) => {
				if (distanceToLine(entry.target) <= SLACK) active = index;
			});
			this.select(active);
		},

		select(index) {
			if (index === this.active) return;
			this.active = index;
			this.apply();
		},

		/**
		 * Move the fill, the dot and the mark to wherever active is now.
		 */
		apply() {
			if (this.entries.length === 0) return;
			const total = this.length || 1;
			const reached = this.reach[this.active] ?? 0;

			this.$refs.fill.setAttribute("stroke-dashoffset", round(this.length - reached));
			this.$refs.dot.style.offsetDistance = `${(reached / total) * 100}%`;

			this.entries.forEach((entry, index) => {
				// aria-current="location" rather than "page": every entry
				// points at the page you are already on, and what is being
				// marked is where in it you have got to.
				if (index === this.active) entry.link.setAttribute("aria-current", "location");
				else entry.link.removeAttribute("aria-current");
			});
		},
	}));
}

function firstLineCentre(element, listTop) {
	const rect = element.getClientRects()[0] ?? element.getBoundingClientRect();
	return rect.top - listTop + rect.height / 2;
}

function place(circle, point, radius) {
	circle.setAttribute("cx", round(point.x));
	circle.setAttribute("cy", round(point.y));
	circle.setAttribute("r", radius);
}

function round(value) {
	return Math.round(value * 100) / 100;
}

function throttle(run) {
	let pending = false;
	return () => {
		if (pending) return;
		pending = true;
		requestAnimationFrame(() => {
			pending = false;
			run();
		});
	};
}
