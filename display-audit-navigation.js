(function () {
  "use strict";

  var destination = new URL("./display-audit-dashboard.html", document.baseURI).href;

  function findDisplayAuditCard(node) {
    if (!(node instanceof Element)) return null;

    var card = node.closest(".top-kpi-row > .kc");
    if (!card) return null;

    var text = (card.textContent || "").replace(/\s+/g, "");
    return text.indexOf("陈列稽核") !== -1 ? card : null;
  }

  function navigate(event) {
    var card = findDisplayAuditCard(event.target);
    if (!card) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    window.location.href = destination;
  }

  window.addEventListener("click", navigate, true);

  window.addEventListener("keydown", function (event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    navigate(event);
  }, true);

  function prepareCard() {
    var cards = document.querySelectorAll(".top-kpi-row > .kc");

    for (var i = 0; i < cards.length; i += 1) {
      var text = (cards[i].textContent || "").replace(/\s+/g, "");
      if (text.indexOf("陈列稽核") === -1) continue;

      cards[i].style.cursor = "pointer";
      cards[i].setAttribute("role", "link");
      cards[i].setAttribute("tabindex", "0");
      cards[i].setAttribute("aria-label", "打开陈列稽核看板");
      cards[i].title = "打开陈列稽核看板";
      break;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", prepareCard, { once: true });
  } else {
    prepareCard();
  }
})();
