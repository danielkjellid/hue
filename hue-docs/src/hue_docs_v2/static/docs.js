// The docs' own Alpine components: a specimen panel's controls, and search.
// Loaded as a classic script before hue's bundle starts Alpine, so both are
// registered by the time it does.

document.addEventListener("alpine:init", () => {
  const Alpine = window.Alpine;

  // A panel's frame: how wide it is drawn, which theme it is drawn in, and a
  // height that follows what is inside it.
  Alpine.data("docsPanel", ({ minHeight = 0, contentId } = {}) => ({
    width: null, // null fills the panel
    theme: null, // null follows the site
    showCode: false,
    minWidth: 320,
    shownWidth: 0,
    sizes: null,
    content: null,

    init() {
      this.sizes = new ResizeObserver(() => {
        this.shownWidth = this.$refs.holder.offsetWidth;
      });
      this.sizes.observe(this.$refs.holder);
      this.$watch("effectiveTheme", () => this.paint());
    },

    destroy() {
      this.sizes?.disconnect();
      this.content?.disconnect();
    },

    get effectiveTheme() {
      return this.theme ?? Alpine.store("theme").resolved;
    },

    maxWidth() {
      // As wide as the panel, less the strip the handle sits in.
      return this.$refs.canvas.clientWidth - 16;
    },

    readout() {
      return `${Math.round(this.shownWidth)}px`;
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
        const height = Math.ceil(content.getBoundingClientRect().height);
        frame.style.height = `${Math.max(minHeight, height)}px`;
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
      return Math.min(this.maxWidth(), Math.max(this.minWidth, Math.round(width)));
    },

    startDrag(event) {
      if (event.button !== 0) return;
      const handle = event.currentTarget;
      const startX = event.clientX;
      const startWidth = this.$refs.holder.offsetWidth;
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
      const current = this.$refs.holder.offsetWidth;
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
    pagefind: null,

    reset() {
      this.query = "";
      this.results = [];
      this.active = -1;
      this.searched = false;
      this.status = "";
    },

    async load() {
      if (!this.pagefind) {
        this.pagefind = await import(`${base}pagefind/pagefind.js`);
        // The index already holds each page's full path, base included.
        await this.pagefind.options({ baseUrl: "/" });
      }
      return this.pagefind;
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

    move(step) {
      if (!this.results.length) return;
      this.active = (this.active + step + this.results.length) % this.results.length;
      this.$nextTick(() =>
        document.getElementById(`docs-search-${this.active}`)?.scrollIntoView({ block: "nearest" }),
      );
    },

    go() {
      const row = this.results[this.active];
      if (row) window.location.href = row.url;
    },
  }));
});
