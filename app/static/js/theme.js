(function () {
  "use strict";

  var root = document.documentElement;
  var button = document.getElementById("theme-toggle");
  if (!button) return;

  var label = button.querySelector(".theme-label");

  function apply(theme) {
    var isDark = theme === "dark";
    root.setAttribute("data-theme", isDark ? "dark" : "light");
    var nextLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
    button.setAttribute("aria-label", nextLabel);
    button.setAttribute("title", nextLabel);
    if (label) label.textContent = isDark ? "Light" : "Dark";
  }

  var saved = null;
  try {
    saved = localStorage.getItem("calendar-theme");
  } catch (error) {
    saved = null;
  }

  apply(saved === "dark" ? "dark" : "light");

  button.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    try {
      localStorage.setItem("calendar-theme", next);
    } catch (error) {
      /* Ignore storage failures. */
    }
  });
})();
