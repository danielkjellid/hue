import Alpine from "alpinejs";
import ajax from "@imacrayon/alpine-ajax";

// Make Alpine available globally
window.Alpine = Alpine;

// Register the ajax plugin
Alpine.plugin(ajax);

// Export a function that configures Alpine with CSRF token
export function configureAlpine(csrfToken) {
  // Configure ajax with CSRF token
  ajax.configure({
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });

  // Start Alpine
  Alpine.start();

  return Alpine;
}

// Also export Alpine and ajax for direct access if needed
export { Alpine, ajax };
