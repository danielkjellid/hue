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
 * What the content scrolls inside, where that is not the page.
 *
 * A table of contents beside a panel is reading something whose top is not
 * the top of the window, and every measurement here is taken from it.
 */
function scrollerOf(element) {
	// From the element itself: the container the headings are in is very
	// often the thing that scrolls them.
	for (let node = element; node; node = node.parentElement) {
		const overflow = getComputedStyle(node).overflowY;
		if (overflow !== "auto" && overflow !== "scroll") continue;
		if (node.scrollHeight > node.clientHeight) return node;
	}
	return null;
}

/**
 * Where a heading sits relative to the line it is reached at.
 *
 * That line is the top of whatever the content scrolls inside, less the
 * scroll-margin the page keeps clear for what it holds up there - which is
 * to say, exactly where clicking the entry would put the heading.
 * Measuring from anywhere further down makes a short section unreachable:
 * click its entry, and the next heading would already have crossed the line.
 */
function distanceToLine(element, top) {
	const margin = parseFloat(getComputedStyle(element).scrollMarginTop) || 0;
	return element.getBoundingClientRect().top - margin - top;
}

/**
 * How far the content can scroll, and whether it has gone all the way.
 *
 * The last section is often too short to fill the screen, so the scroll
 * stops before its heading ever reaches the line, and once it can go no
 * further that heading is the one being read. A page with nothing to
 * scroll never counts as at its end.
 */
function scrollState(scroller) {
	const page = scroller ?? document.scrollingElement;
	const room = page.scrollHeight - page.clientHeight;
	const scrolls = room > 2;
	return { page, scrolls, atEnd: scrolls && page.scrollTop >= room - 2 };
}

export function registerTocData(Alpine) {
	Alpine.data("hueToc", ({ of = "main", headings = "h2, h3" } = {}) => ({
		active: 0,
		// The entry the reader clicked, until the scroll can show it itself.
		chosen: null,
		entries: [],
		reach: [],
		length: 0,

		// Declared, every one of them, because Alpine writes a property its
		// data object never mentioned to the outermost scope on the page
		// instead of to this component - where the next table of contents
		// would find it and take it for its own.
		container: null,
		onMove: null,
		onContent: null,
		onSettle: null,
		onHistory: null,
		sizes: null,
		content: null,

		init() {
			this.build();

			this.onMove = throttle(() => this.read());
			this.onContent = throttle(() => this.build());
			// Not throttled: what calls it is already batched to once a
			// frame, and drawing changes nothing that could call it back.
			this.onSettle = () => {
				this.draw();
				this.read();
			};

			// Capturing, so a page that scrolls inside a container rather
			// than the window is heard too. Scroll events do not bubble.
			document.addEventListener("scroll", this.onMove, true);
			window.addEventListener("resize", this.onMove);
			// A frame later: the browser scrolls to the fragment after
			// popstate, which would undo a container position put back here.
			this.onHistory = (event) => requestAnimationFrame(() => this.revisit(event.state));
			window.addEventListener("popstate", this.onHistory);

			// The nav's own width decides where the labels wrap, which is
			// what the rail is drawn from. It fires once on observe too,
			// which is the pass that corrects whatever init measured before
			// the stylesheets had arrived.
			this.sizes = new ResizeObserver(this.onSettle);
			this.sizes.observe(this.$root);

			// Content replaced by a fragment is a different set of headings.
			// Attributes are not watched, or setting an id would call this
			// straight back. Nor is this component's own list, which build
			// rewrites: when the contents sit inside what they list, as they
			// do in the default main, every build would start the next one.
			if (this.container) {
				this.content = new MutationObserver((records) => {
					if (records.some((record) => !this.$root.contains(record.target))) {
						this.onContent();
					}
				});
				this.content.observe(this.container, { childList: true, subtree: true });
			}

			// The stylesheets in the head may not have arrived when Alpine
			// started, and until they have there is nothing to measure.
			if (document.readyState !== "complete") {
				window.addEventListener("load", this.onSettle, { once: true });
			}

			// Text moves when the real typeface arrives, and every number
			// here came from where the text was.
			document.fonts?.ready.then(() => this.onSettle());
		},

		destroy() {
			document.removeEventListener("scroll", this.onMove, true);
			window.removeEventListener("resize", this.onMove);
			window.removeEventListener("popstate", this.onHistory);
			window.removeEventListener("load", this.onSettle);
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

			this.container = container;

			this.entries = found.map((element, index) => ({
				element,
				target: anchorFor(element, found, taken),
				depth: levels[index] - top,
			}));

			// A page with no headings has no contents, and a title over an
			// empty list is worse than nothing at all.
			this.$root.hidden = this.entries.length === 0;

			this.chosen = null;
			const list = this.$refs.list;
			list.replaceChildren();
			for (const [index, entry] of this.entries.entries()) {
				const row = this.$refs.row.content.firstElementChild.cloneNode(true);
				entry.link = row.querySelector("a");
				entry.link.href = `#${entry.target.id}`;
				entry.link.addEventListener("click", (event) => this.follow(event, index));
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

			// Looked for every time rather than remembered: a panel only
			// starts scrolling once it has enough in it, which can be long
			// after this was set up, and a short walk up the ancestors costs
			// less than being wrong about it.
			const scroller = scrollerOf(this.container);

			// A heading that is not rendered, in a closed disclosure say,
			// measures as sitting at the very top and would be reached from
			// the first pixel. It keeps its entry, since opening it changes
			// no child list and so would never bring the entry back, but it
			// is never where the reader has got to.
			const shown = entries
				.map((entry, index) => index)
				.filter((index) => entries[index].element.getClientRects().length > 0);

			// A click wins where the scroll could not follow it: an early
			// entry on a page already at its end, or any entry on a page
			// with nothing to scroll. The first scroll that moves clears it.
			const { scrolls, atEnd } = scrollState(scroller);
			if (this.chosen !== null && (atEnd || !scrolls)) {
				this.select(this.chosen);
				return;
			}
			this.chosen = null;

			if (atEnd) {
				this.select(shown.at(-1) ?? 0);
				return;
			}

			const top = scroller ? scroller.getBoundingClientRect().top : 0;

			// The first heading stands for everything above it, including
			// whatever comes before it on the page.
			let active = shown[0] ?? 0;
			for (const index of shown) {
				if (distanceToLine(entries[index].target, top) <= SLACK) active = index;
			}
			this.select(active);
		},

		/**
		 * Go to an entry's heading by scrolling only what holds it.
		 *
		 * Following the link natively would scroll every ancestor document
		 * as well, moving the page around contents that sit in a scrolling
		 * panel or an iframe. Focus goes to the heading, as it would after
		 * a skip link, so the next Tab carries on from the section rather
		 * than from the list.
		 */
		follow(event, index) {
			// A new tab or window is the browser's to open.
			if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
				return;
			}
			event.preventDefault();

			const { target } = this.entries[index];
			const scroller = scrollerOf(this.container);

			if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
			target.focus({ preventScroll: true });
			// A history entry, as following the link would have made, unless
			// the link is the one already in the address bar. Pushed before
			// the scroll, because the browser files the page's scroll
			// position under the entry being left, and Back returns to it.
			// It files nothing for a container, so that goes in by hand.
			if (decodeURIComponent(location.hash.slice(1)) !== target.id) {
				if (scroller) {
					history.replaceState({ ...history.state, hueTocScroll: scroller.scrollTop }, "");
				}
				// No state of its own: one copied from a swapped entry would
				// carry __ajax, and Alpine AJAX reloads the page on Back to that.
				history.pushState(null, "", `#${target.id}`);
			}
			this.reveal(target, scroller);

			this.chosen = index;
			this.select(index);
		},

		/**
		 * Scroll what holds a heading so it sits at the top.
		 *
		 * A container that is itself off screen would scroll the heading to a
		 * top nobody can see, so this document scrolls to bring the container
		 * in, as a fragment link would. Ancestor documents stay put.
		 */
		reveal(target, scroller) {
			const top = scroller ? scroller.getBoundingClientRect().top : 0;
			// The page's own scroll-behavior still applies.
			scrollState(scroller).page.scrollBy({ top: distanceToLine(target, top) });
			if (!scroller) return;

			const landing = top + (parseFloat(getComputedStyle(target).scrollMarginTop) || 0);
			if (landing < 0 || landing + target.offsetHeight > document.documentElement.clientHeight) {
				document.scrollingElement.scrollBy({ top });
			}
		},

		/**
		 * Follow Back and Forward to the entry they land on.
		 *
		 * The browser restores the page's scroll, and the scroll moves the
		 * mark, but when nothing scrolls only the address says where the
		 * reader is. A container gets back the position follow saved for it,
		 * or failing that the heading the address names.
		 */
		revisit(state) {
			const id = decodeURIComponent(location.hash.slice(1));
			const index = this.entries.findIndex((entry) => entry.target.id === id);
			const scroller = scrollerOf(this.container);

			if (scroller && state?.hueTocScroll !== undefined) {
				scroller.scrollTop = state.hueTocScroll;
			} else if (scroller && index !== -1) {
				this.reveal(this.entries[index].target, scroller);
			}

			this.chosen = index === -1 ? null : index;
			if (index === -1) this.read();
			else this.select(index);
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
