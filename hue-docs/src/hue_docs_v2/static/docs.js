// The docs' own Alpine components: a specimen panel's controls, and search.
// Loaded as a classic script before hue's bundle starts Alpine, so both are
// registered by the time it does.

document.addEventListener("alpine:init", () => {
  const Alpine = window.Alpine;

  // Whether the OS asks for dark. hue's theme store reads it when asked but
  // does not track it, so a panel following "system" would not repaint.
  const dark = window.matchMedia("(prefers-color-scheme: dark)");
  const os = Alpine.reactive({ dark: dark.matches });
  dark.addEventListener("change", (event) => (os.dark = event.matches));

  // A panel's frame: how wide it is drawn, which theme it is drawn in, and a
  // height that follows what is inside it.
  Alpine.data("docsPanel", ({ minHeight = 0, maxWidth, contentId, width = null, minFill = 0 } = {}) => ({
    // A start width only where the presets are shown to leave it. On a
    // narrower screen it would be drawn at a third of its size.
    width: window.matchMedia("(min-width: 768px)").matches ? width : null, // null fills
    theme: null, // a choice as hue's theme store has them; null follows the site
    showCode: false,
    minWidth: 320,
    maxWidth,
    room: 0, // how wide the panel can draw the frame
    height: 0, // the frame's content height, unscaled
    sizes: null,
    content: null,
    themes: null,

    init() {
      this.sizes = new ResizeObserver(() => {
        // Less the strip the handle sits in.
        this.room = this.$refs.canvas.clientWidth - 16;
      });
      this.sizes.observe(this.$refs.canvas);
      this.$watch("choice", () => this.paint());
      this.$watch("effectiveTheme", () => this.paint());
    },

    destroy() {
      this.sizes?.disconnect();
      this.content?.disconnect();
      this.themes?.disconnect();
    },

    get choice() {
      return this.theme ?? Alpine.store("theme").choice;
    },

    get effectiveTheme() {
      if (this.choice !== "system") return this.choice;
      return os.dark ? "dark" : "light";
    },

    // The viewport the example sees, which can be wider than the panel. A
    // panel that fills is still drawn at least minFill wide, and scrolls.
    get shown() {
      return this.width ?? Math.max(this.room, minFill);
    },

    // A viewport wider than the panel is drawn at full width and scaled
    // down, so the frame's media queries still see the width chosen.
    get scale() {
      return this.width !== null && this.width > this.room ? this.room / this.width : 1;
    },

    // Objects rather than strings: Alpine sets a string as the whole style
    // attribute, which would drop the height the frame is given below.
    holderStyle() {
      if (this.width === null) return { width: "100%", minWidth: `${minFill}px` };
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
      // A ThemeSwitcher in the frame sets its own theme, which the bar follows.
      // Read from the frame's store: under "system" its data-theme also moves
      // with the OS, and that is not a choice the reader made.
      this.themes?.disconnect();
      this.themes = new MutationObserver(() => {
        const store = frame.contentWindow.Alpine?.store("theme");
        const choice = store ? store.choice : doc.documentElement.getAttribute("data-theme");
        if (choice !== this.choice) this.theme = choice;
      });
      this.themes.observe(doc.documentElement, { attributeFilter: ["data-theme"] });
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
      const win = this.$refs.frame?.contentWindow;
      const store = win?.Alpine?.store("theme");
      if (!store) {
        win?.document.documentElement.setAttribute("data-theme", this.effectiveTheme);
        return;
      }
      // Through the frame's store, so a ThemeSwitcher in it shows the choice.
      // Not select(), which would save the panel's choice as the site's.
      store.choice = this.choice;
      store.apply();
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
    // go to the narrowest and the widest. Fill is the first preset, shown at
    // every width.
    nudge(event) {
      const current = this.shown;
      // Toward the handle's own side widens, as dragging does.
      const step = (event.shiftKey ? 64 : 16) * (document.dir === "rtl" ? -1 : 1);
      const moves = {
        ArrowLeft: () => this.clamp(current - step),
        ArrowRight: () => this.clamp(current + step),
        Home: () => this.minWidth,
        End: () => this.maxWidth,
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
      // An exact title first: "button" finds Button before ButtonGroup.
      const exact = (page) => page.meta.title.toLowerCase() === query.toLowerCase();
      pages.sort((a, b) => exact(b) - exact(a));
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
      if (!row) return;
      const to = new URL(row.url, location.href);
      if (to.pathname !== location.pathname || !to.hash) {
        location.href = row.url;
        return;
      }
      // A section of this page: nothing unloads, so the dialog has to close
      // first. Once its trap has handed focus back and let the page scroll,
      // which it does a task later, the section takes the focus.
      this.open = false;
      this.$nextTick(() =>
        setTimeout(() => {
          location.href = row.url;
          const target = document.getElementById(decodeURIComponent(to.hash.slice(1)));
          if (!target) return;
          if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
          target.focus({ preventScroll: true });
        }),
      );
    },

    // A click on a result goes the way Enter does, so one on this page
    // closes the dialog too. A modified click is left to open a tab.
    follow(event, index) {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }
      event.preventDefault();
      this.active = index;
      this.go();
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
    if (!link) return;
    const modified =
      event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
    if (link.getAttribute("href").startsWith("#")) {
      // A plain click is handled below, once the specimen's own handlers ran.
      if (!modified) return;
    } else if (new URL(link.href).pathname.includes("/demos/")) {
      return;
    }
    event.preventDefault();
  };
  // auxclick too, or a middle click opens the made-up path in a new tab.
  document.addEventListener("click", guard, true);
  document.addEventListener("auxclick", guard, true);
  // Following an anchor would add an entry to the docs page's history, so
  // the frame moves to it in place.
  window.addEventListener("click", (event) => {
    const link = event.target.closest?.("a[href^='#']");
    if (!link || event.defaultPrevented) return;
    event.preventDefault();
    location.replace(link.href);
  });
  document.addEventListener(
    "submit",
    (event) => {
      // The attribute rather than form.action, which a control named
      // "action" replaces; and a submitter's formaction wins over it.
      const submitter = event.submitter;
      const action = submitter?.hasAttribute("formaction")
        ? submitter.formAction
        : new URL(event.target.getAttribute("action") ?? "", location.href).href;
      if (new URL(action).pathname.includes("/demos/")) return;
      event.preventDefault();
    },
    true,
  );
  // A demo's swaps would otherwise push entries onto the docs page's history,
  // so Back would walk the demo before it left the page.
  history.pushState = history.replaceState.bind(history);
  // Escape is passed on in the capture phase, before a component in this
  // frame that takes the key, such as an open tooltip, stops it. The docs
  // page sends it on to the frame under the pointer.
  window.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape") window.top.docsEscape?.(window);
    },
    true,
  );
  // Every other key goes to the docs page too, so its shortcuts work with
  // focus in a specimen: once the specimen has had the key, and unless it
  // took it. In a field only a chord with Command or Control is a shortcut,
  // as on the page, which cannot see the field. The selector is the one
  // hue's shortcuts.js reads as a field.
  const field =
    "input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit])" +
    ":not([type=reset]):not([type=range]):not([type=color]):not([type=file]):not([type=image])," +
    " textarea, select, [role=combobox], [role=listbox], [role=menu]";
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" || event.defaultPrevented || event.isComposing) return;
    const typing = event.target.isContentEditable || event.target.closest?.(field);
    // Nor from inside a modal open in here, as hue's shortcuts run none
    // outside an open modal; a chord still opens the site's search.
    const modal = [...document.querySelectorAll('[aria-modal="true"]')].some((el) =>
      el.checkVisibility(),
    );
    if ((typing || modal) && !event.metaKey && !event.ctrlKey) return;
    const top = window.top;
    const forwarded = new top.KeyboardEvent("keydown", {
      key: event.key,
      code: event.code,
      metaKey: event.metaKey,
      ctrlKey: event.ctrlKey,
      altKey: event.altKey,
      shiftKey: event.shiftKey,
      repeat: event.repeat,
      modifierAltGraph: event.getModifierState("AltGraph"),
      cancelable: true,
    });
    // The search takes focus to the docs page, and its trap hands it back
    // to this frame rather than to what had it in here.
    let searched = false;
    const note = () => (searched = true);
    top.addEventListener("docs-search", note);
    top.dispatchEvent(forwarded);
    top.removeEventListener("docs-search", note);
    if (!forwarded.defaultPrevented) return;
    event.preventDefault();
    const had = document.activeElement;
    if (!searched || had === document.body) return;
    window.addEventListener(
      "focus",
      // A task later, once a menu or popover that losing focus closes
      // (below) has closed. Its item goes with it, so focus goes to the
      // control that opened it, found as the trigger beside the panel.
      () =>
        setTimeout(() => {
          if (document.activeElement !== document.body) return;
          const panel = had.closest('[role="menu"], [role="dialog"], [role="listbox"]');
          let host = panel?.parentElement;
          while (host && !host.querySelector("[data-hue-trigger]")) host = host.parentElement;
          const trigger = host?.querySelector("[data-hue-trigger]");
          const closed = trigger?.getAttribute("aria-expanded") === "false";
          (closed ? trigger : had).focus();
        }),
      { once: true },
    );
  });
  // A menu or a popover closes on a click outside it, which a click on the
  // docs page never is to this frame. Focus moving to the docs page or
  // another frame stands in for one. Focus going to another window or tab
  // does not, so a popover stays open while the reader looks elsewhere.
  window.addEventListener("blur", () =>
    setTimeout(() => {
      // Dispatched rather than click(), which does nothing while the
      // search's trap holds this frame inert.
      if (!window.top.document.hasFocus()) return;
      document.body?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }),
  );
}

if (window.self === window.top) {
  // Escape goes to the document with focus, while a tooltip opened by
  // hovering, or an overlay left open when focus moved on, waits in the
  // frame under the pointer. Passed on to that frame, from the docs page or
  // from another frame, unless it already heard it, and only while something
  // in it is open: a page-wide Escape, such as the one that clears a table's
  // selection, belongs to the frame with focus. Sent from the element with
  // focus in there, or else from the overlay, since an overlay hears the key
  // on its own root and a tooltip on the window.
  const OPEN = '[role="tooltip"], [role="dialog"], [role="alertdialog"], [role="menu"]';
  let hovered = null;
  document.addEventListener("mouseover", (event) => {
    hovered = event.target instanceof HTMLIFrameElement ? event.target : null;
  });
  document.addEventListener("mouseout", (event) => {
    if (!event.relatedTarget) hovered = null;
  });
  window.docsEscape = (source) => {
    const win = hovered?.isConnected ? hovered.contentWindow : null;
    if (!win || win === source) return;
    const open = [...win.document.querySelectorAll(OPEN)].filter((el) => el.checkVisibility());
    if (!open.length) return;
    const active = win.document.activeElement;
    const from = open.some((el) => el.contains(active)) ? active : open.at(-1);
    from.dispatchEvent(new win.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  };

  // The sidebar is longer than the window, so the current page's entry is
  // brought into its scroller on load, and when the drawer opens on a phone.
  window.docsShowCurrent = (scroller) => {
    const item = scroller.querySelector('[aria-current="page"]');
    if (!item || !scroller.clientHeight) return;
    const top = item.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
    if (top >= 0 && top + item.offsetHeight <= scroller.clientHeight) return;
    scroller.scrollTop += top - (scroller.clientHeight - item.offsetHeight) / 2;
  };
  window.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape") window.docsEscape(window);
    },
    true,
  );

  // Frames paint first in the theme saved under their own key (FramePage in
  // panel.py), so it follows the site's choice, and a ThemeSwitcher demo
  // changes it only until the site's theme next changes.
  document.addEventListener("alpine:initialized", () => {
    window.Alpine.effect(() => {
      const choice = window.Alpine.store("theme").choice;
      try {
        localStorage.setItem("hue-docs-frame-theme", choice);
      } catch {
        // Without storage a frame paints the system theme first.
      }
    });
  });

  // A page lands before the frames on it have loaded, and each one that
  // grows moves what is below it. Until the reader scrolls, clicks or types,
  // or focus moves into a frame, the page keeps going back to the place it
  // is meant to show: on arriving by a link, the link's target; on Back and
  // reload, where the reader left it. The browser restores that too, but
  // before the frames have grown, and then moves with them.
  const how = performance.getEntriesByType("navigation")[0]?.type;
  const key = `docs-scroll:${location.href}`;
  addEventListener("pagehide", () => {
    try {
      sessionStorage.setItem(key, String(window.scrollY));
    } catch {
      // Without storage the browser's own restoring is all there is.
    }
  });
  let saved = null;
  if (how === "back_forward" || how === "reload") {
    try {
      saved = sessionStorage.getItem(key);
    } catch {
      // As above.
    }
  }
  const target =
    how === "navigate" &&
    location.hash &&
    document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target || saved !== null) {
    let landed = null;
    const settle = new ResizeObserver(() => {
      if (target) target.scrollIntoView({ block: "start", behavior: "instant" });
      else window.scrollTo({ top: Number(saved), behavior: "instant" });
      landed = window.scrollY;
    });
    const stop = () => {
      settle.disconnect();
      for (const type of ["pointerdown", "keydown", "wheel", "touchstart", "blur"]) {
        window.removeEventListener(type, stop, true);
      }
      window.removeEventListener("scroll", moved);
    };
    // A scroll that is not this one's is the reader's, except on Back and
    // reload, where the browser scrolls too.
    const moved = () => {
      if (target && landed !== null && Math.abs(window.scrollY - landed) > 1) stop();
    };
    settle.observe(document.body);
    for (const type of ["pointerdown", "keydown", "wheel", "touchstart", "blur"]) {
      window.addEventListener(type, stop, { capture: true, passive: true });
    }
    window.addEventListener("scroll", moved, { passive: true });
  }
}
