// The docs' own Alpine components: a specimen panel's controls, and search.
// Loaded as a classic script before hue's bundle starts Alpine, so both are
// registered by the time it does.

document.addEventListener("alpine:init", () => {
  const Alpine = window.Alpine;

  // A panel's frame: how wide it is drawn, which theme it is drawn in, and a
  // height that follows what is inside it.
  Alpine.data("docsPanel", ({ minHeight = 0 } = {}) => ({
    width: null, // null fills the panel
    theme: null, // null follows the site
    showCode: false,
    minWidth: 320,
    shownWidth: 0,
    sizes: null,

    init() {
      this.sizes = new ResizeObserver(() => {
        this.shownWidth = this.$refs.holder.offsetWidth;
      });
      this.sizes.observe(this.$refs.holder);
      this.$watch("effectiveTheme", () => this.paint());
    },

    destroy() {
      this.sizes?.disconnect();
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
      const content = doc.getElementById("frame");
      // A lazy frame loads about:blank first, which has none.
      if (!content) return;
      const fit = () => {
        frame.style.height = `${Math.max(minHeight, Math.ceil(content.getBoundingClientRect().height))}px`;
      };
      new ResizeObserver(fit).observe(content);
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
      const handle = event.currentTarget;
      const startX = event.clientX;
      const startWidth = this.$refs.holder.offsetWidth;
      handle.setPointerCapture(event.pointerId);
      // The frame swallows pointer events over it, which would drop the drag
      // whenever the pointer crossed into it.
      this.$refs.frame.style.pointerEvents = "none";
      const move = (e) => {
        const dir = document.dir === "rtl" ? -1 : 1;
        this.width = this.clamp(startWidth + dir * (e.clientX - startX));
      };
      const end = () => {
        this.$refs.frame.style.pointerEvents = "";
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", end);
        handle.removeEventListener("pointercancel", end);
      };
      handle.addEventListener("pointermove", move);
      handle.addEventListener("pointerup", end);
      handle.addEventListener("pointercancel", end);
    },

    // The handle's keyboard: arrows step, shift steps further, Home and End
    // go to the narrowest and the full width.
    nudge(event) {
      const current = this.$refs.holder.offsetWidth;
      const step = event.shiftKey ? 64 : 16;
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
        await this.pagefind.options({ baseUrl: base });
      }
      return this.pagefind;
    },

    async search() {
      const query = this.query.trim();
      if (!query) {
        this.reset();
        return;
      }
      const pagefind = await this.load();
      const found = await pagefind.debouncedSearch(query, {}, 120);
      // Superseded by a later keystroke.
      if (found === null) return;
      const pages = await Promise.all(found.results.slice(0, 8).map((r) => r.data()));
      this.results = pages.flatMap((page) => {
        const sections = page.sub_results
          .filter((sub) => sub.url !== page.url)
          .slice(0, 3)
          .map((sub) => ({
            url: sub.url,
            title: sub.title,
            page: page.meta.title,
            section: true,
            excerpt: sub.excerpt,
          }));
        const own = { url: page.url, title: page.meta.title, page: "", section: false, excerpt: page.excerpt };
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
