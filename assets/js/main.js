// FD432Games — small progressive enhancements. The site works without JS.
(function () {
  "use strict";

  // Remember the language the visitor picked with the EN/PL switch,
  // so the automatic redirect in <head> never overrides a manual choice.
  document.querySelectorAll("[data-set-lang]").forEach(function (link) {
    link.addEventListener("click", function () {
      try { localStorage.setItem("fd-lang", link.getAttribute("data-set-lang")); } catch (e) {}
    });
  });

  // Screenshot lightbox
  var dialog = document.querySelector(".lightbox");
  if (!dialog || typeof dialog.showModal !== "function") return;
  var img = dialog.querySelector("img");

  document.querySelectorAll(".shot").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var thumb = btn.querySelector("img");
      img.src = btn.getAttribute("data-full");
      img.alt = thumb ? thumb.alt : "";
      dialog.showModal();
    });
  });

  dialog.querySelector(".lb-close").addEventListener("click", function () { dialog.close(); });
  dialog.addEventListener("click", function (e) {
    if (e.target === dialog) dialog.close();
  });
  dialog.addEventListener("close", function () { img.removeAttribute("src"); });
})();
