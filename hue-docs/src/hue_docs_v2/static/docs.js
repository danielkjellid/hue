// The docs' own Alpine components: a specimen panel's controls, and search.
// Loaded as a classic script before hue's bundle starts Alpine, so both are
// registered by the time it does.

document.addEventListener("alpine:init", () => {
  const Alpine = window.Alpine;

  // A panel's frame: how wide it is drawn, which theme it is drawn in, and a
  // height that follows what is inside it.
  Alpine.data("docsPanel", ({ minHeight = 0, maxWidth, contentId } = {}) => ({
    width: null, // null fills the panel
    theme: null, // null follows the site
    showCode: false,
    minWidth: 320,
    maxWidth,
    room: 0, // how wide the panel can draw the frame
    height: 0, // the frame's content height, unscaled
    sizes: null,
    content: null,

    init() {
      this.sizes = new ResizeObserver(() => {
        // Less the strip the handle sits in.
        this.room = this.$refs.canvas.clientWidth - 16;
      });
      this.sizes.observe(this.$refs.canvas);
      this.$watch("effectiveTheme", () => this.paint());
    },

    destroy() {
      this.sizes?.disconnect();
      this.content?.disconnect();
    },

    get effectiveTheme() {
      return this.theme ?? Alpine.store("theme").resolved;
    },

    // The viewport the example sees, which can be wider than the panel.
    get shown() {
      return this.width ?? this.room;
    },

    // A viewport wider than the panel is drawn at full width and scaled
    // down, so the frame's media queries still see the width chosen.
    get scale() {
      return this.width !== null && this.width > this.room ? this.room / this.width : 1;
    },

    // Objects rather than strings: Alpine sets a string as the whole style
    // attribute, which would drop the height the frame is given below.
    holderStyle() {
      if (this.width === null) return { width: "100%" };
      if (this.scale === 1) return { width: `${this.width}px` };
      return {
        width: `${this.room}px`,
        height: `${Math.ceil(this.height * this.scale)}px`,
      };
    },

    frameStyle() {
      if (this.scale === 1) return {};
      return {
        width: `${this.width}px`,
        transform: `scale(${this.scale})`,
        transformOrigin: document.dir === "rtl" ? "top right" : "top left",
      };
    },

    readout() {
      const width = `${Math.round(this.shown)}px`;
      return this.scale < 1 ? `${width} at ${Math.round(this.scale * 100)}%` : width;
    },

    // Called on every load of the frame, so a frame that reloads keeps its
    // theme and its height tracking.
    attach() {
      const frame = this.$refs.frame;
      const doc = frame.contentDocument;
      if (!doc) return;
      this.paint();
      // The content, not the body: the body is at least as tall as the
      // frame, so measuring it could only ever grow the frame.
      const content = doc.getElementById(contentId);
      // A lazy frame loads about:blank first, which has none.
      if (!content) return;
      const fit = () => {
        this.height = Math.max(minHeight, Math.ceil(content.getBoundingClientRect().height));
        frame.style.height = `${this.height}px`;
      };
      // One observer per frame: a reload replaces the document it watched.
      this.content?.disconnect();
      this.content = new ResizeObserver(fit);
      this.content.observe(content);
      fit();
    },

    paint() {
      const doc = this.$refs.frame?.contentDocument;
      doc?.documentElement.setAttribute("data-theme", this.effectiveTheme);
    },

    clamp(width) {
      return Math.min(this.maxWidth, Math.max(this.minWidth, Math.round(width)));
    },

    startDrag(event) {
      if (event.button !== 0) return;
      const handle = event.currentTarget;
      const startX = event.clientX;
      const startWidth = this.shown;
      handle.setPointerCapture(event.pointerId);
      // The frame swallows pointer events over it, which would drop the drag
      // whenever the pointer crossed into it.
      this.$refs.frame.style.pointerEvents = "none";
      // One signal removes every listener the drag added.
      const stop = new AbortController();
      const listening = { signal: stop.signal };
      const end = () => {
        this.$refs.frame.style.pointerEvents = "";
        stop.abort();
      };
      handle.addEventListener(
        "pointermove",
        (e) => {
          const dir = document.dir === "rtl" ? -1 : 1;
          this.width = this.clamp(startWidth + dir * (e.clientX - startX));
        },
        listening,
      );
      // Capture can be taken away without a pointerup, which would otherwise
      // leave the frame deaf to the pointer.
      for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
        handle.addEventListener(type, end, listening);
      }
    },

    // The handle's keyboard: arrows step, shift steps further, Home and End
    // go to the narrowest and the full width.
    nudge(event) {
      const current = this.shown;
      // Toward the handle's own side widens, as dragging does.
      const step = (event.shiftKey ? 64 : 16) * (document.dir === "rtl" ? -1 : 1);
      const moves = {
        ArrowLeft: () => this.clamp(current - step),
        ArrowRight: () => this.clamp(current + step),
        Home: () => this.minWidth,
        End: () => null,
      };
      if (!(event.key in moves)) return;
      event.preventDefault();
      this.width = moves[event.key]();
    },
  }));

  // Search over the Pagefind index, loaded the first time it is used.
  Alpine.data("docsSearch", (base) => ({
    query: "",
    results: [],
    active: -1,
    searched: false,
    status: "",
    loading: null,

    reset() {
      this.query = "";
      this.results = [];
      this.active = -1;
      this.searched = false;
      this.status = "";
    },

    // Caches the promise, so every keystroke before the first load finishes
    // waits on that one load, and the latest query still wins.
    load() {
      this.loading ??= import(`${base}pagefind/pagefind.js`).then(async (pagefind) => {
        // The index already holds each page's full path, base included.
        await pagefind.options({ baseUrl: "/" });
        return pagefind;
      });
      return this.loading;
    },

    async search() {
      const query = this.query.trim();
      if (!query) {
        this.reset();
        return;
      }
      let pagefind;
      try {
        pagefind = await this.load();
      } catch {
        this.status = "Search is not available. Build the site to index it.";
        return;
      }
      const found = await pagefind.debouncedSearch(query, {}, 120);
      // Superseded by a later keystroke.
      if (found === null) return;
      const pages = await Promise.all(found.results.slice(0, 8).map((r) => r.data()));
      // The box changed while this search ran, cleared or closed, so its
      // results answer a question nobody is asking any more.
      if (this.query.trim() !== query) return;
      this.results = pages.flatMap((page) => {
        const sections = page.sub_results
          .filter((sub) => sub.url !== page.url)
          .slice(0, 3)
          .map((sub) => ({
            url: sub.url,
            title: sub.title,
            page: page.meta.title,
            excerpt: sub.excerpt,
          }));
        const own = {
          url: page.url,
          title: page.meta.title,
          page: "",
          excerpt: page.excerpt,
        };
        return [own, ...sections];
      });
      this.searched = true;
      this.active = this.results.length ? 0 : -1;
      const count = this.results.length;
      this.status = count ? `${count} result${count === 1 ? "" : "s"}` : "No results";
    },

    // An empty box lists the site's shortcuts, drawn by the server, and a
    // query lists the results. The keys move through whichever is shown.
    listing() {
      return this.query.trim() ? "results" : "shortcuts";
    },

    optionId(index) {
      return this.listing() === "results" ? `docs-search-${index}` : `docs-shortcut-${index}`;
    },

    count() {
      return this.listing() === "results"
        ? this.results.length
        : document.querySelectorAll("[id^='docs-shortcut-']").length;
    },

    move(step) {
      const count = this.count();
      if (!count) return;
      this.active =
        this.active < 0 ? (step > 0 ? 0 : count - 1) : (this.active + step + count) % count;
      this.$nextTick(() =>
        document.getElementById(this.optionId(this.active))?.scrollIntoView({ block: "nearest" }),
      );
    },

    go() {
      if (this.active < 0) return;
      if (this.listing() === "shortcuts") {
        document.getElementById(this.optionId(this.active))?.firstElementChild?.click();
        return;
      }
      const row = this.results[this.active];
      if (row) window.location.href = row.url;
    },
  }));
});

// Inside a panel's frame, a specimen's link or form would load a made-up
// path, or the frame's own GET-only one, into the frame. Links and forms to
// the demo routes, which the live examples use, and links within the page
// still work.
if (window.self !== window.top) {
  const guard = (event) => {
    const link = event.target.closest?.("a[href]");
    if (!link || link.getAttribute("href").startsWith("#")) return;
    if (new URL(link.href).pathname.includes("/demos/")) return;
    event.preventDefault();
  };
  // auxclick too, or a middle click opens the made-up path in a new tab.
  document.addEventListener("click", guard, true);
  document.addEventListener("auxclick", guard, true);
  document.addEventListener(
    "submit",
    (event) => {
      if (new URL(event.target.action).pathname.includes("/demos/")) return;
      event.preventDefault();
    },
    true,
  );
  // A demo's swaps would otherwise push entries onto the docs page's history,
  // so Back would walk the demo before it left the page.
  history.pushState = history.replaceState.bind(history);
}
