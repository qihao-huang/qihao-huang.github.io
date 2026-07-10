/**
 * Shared light/dark theme for Canvas static pages.
 * Modes: system | light | dark  (localStorage key: canvas-theme-mode)
 *
 * Usage in each canvas HTML:
 * 1. In <head>, before CSS: <script src="canvas-theme.js" data-boot></script>
 *    OR inline the boot snippet (see boot()).
 * 2. In topbar: include .theme-switch markup (or call CanvasTheme.mount()).
 * 3. At end of body: CanvasTheme.init()
 */
(function (global) {
  var KEY = "canvas-theme-mode";

  function readMode() {
    try {
      var m = localStorage.getItem(KEY) || "system";
      return m === "light" || m === "dark" || m === "system" ? m : "system";
    } catch (e) {
      return "system";
    }
  }

  function applyMode(mode) {
    var root = document.documentElement;
    if (mode === "light" || mode === "dark") root.setAttribute("data-theme", mode);
    else root.removeAttribute("data-theme");
    try {
      localStorage.setItem(KEY, mode);
    } catch (e) {}
    document.querySelectorAll(".theme-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-theme-mode") === mode);
    });
  }

  /** Call synchronously in <head> to avoid FOUC. */
  function boot() {
    applyMode(readMode());
  }

  function switchMarkup() {
    return (
      '<div class="theme-switch" role="group" aria-label="主题切换" title="主题切换">' +
      '<button type="button" class="theme-btn" data-theme-mode="system">自动</button>' +
      '<button type="button" class="theme-btn" data-theme-mode="light">浅色</button>' +
      '<button type="button" class="theme-btn" data-theme-mode="dark">深色</button>' +
      "</div>"
    );
  }

  /**
   * Ensure topbar has theme switch. Looks for .topbar-actions or creates it
   * inside .topbar (right side).
   */
  function mount() {
    var existing = document.querySelector(".theme-switch");
    if (!existing) {
      var topbar = document.querySelector(".topbar");
      if (!topbar) return;
      var actions = topbar.querySelector(".topbar-actions");
      if (!actions) {
        actions = document.createElement("div");
        actions.className = "topbar-actions";
        // Move trailing tiny/meta into actions if present as last child text node sibling
        var last = topbar.lastElementChild;
        if (last && last !== topbar.querySelector(".crumb") && !last.classList.contains("theme-switch")) {
          actions.appendChild(last);
        }
        topbar.appendChild(actions);
      }
      actions.insertAdjacentHTML("afterbegin", switchMarkup());
    }
    applyMode(readMode());
    document.querySelectorAll(".theme-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyMode(btn.getAttribute("data-theme-mode"));
      });
    });
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
        if (readMode() === "system") applyMode("system");
      });
    } catch (e) {}
  }

  function init() {
    mount();
  }

  // Auto-boot when loaded with data-boot, or as classic script in head
  if (document.currentScript && document.currentScript.hasAttribute("data-boot")) {
    boot();
  } else if (document.readyState === "loading" && document.head && document.head.contains(document.currentScript)) {
    boot();
  }

  global.CanvasTheme = { KEY: KEY, boot: boot, applyMode: applyMode, readMode: readMode, init: init, mount: mount, switchMarkup: switchMarkup };
})(typeof window !== "undefined" ? window : this);
