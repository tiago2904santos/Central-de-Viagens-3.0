(function () {
  "use strict";

  function hydrateIframe(root) {
    var frame = root.querySelector(".document-inline-viewer__frame[data-src]");
    if (!frame) return;
    var src = frame.getAttribute("data-src");
    if (!src || frame.getAttribute("src")) return;
    frame.setAttribute("src", src);
  }

  document.querySelectorAll("[data-lazy-inline]").forEach(function (card) {
    card.addEventListener("toggle", function () {
      if (card.open) {
        hydrateIframe(card);
      }
    });
  });
})();
