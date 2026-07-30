(function () {
  "use strict";

  function isDisplayAuditCard(card) {
    return card && /陈列稽核/.test(card.textContent || "");
  }

  function addNavigationLink(card) {
    if (!isDisplayAuditCard(card) || card.querySelector(".display-audit-card-link")) {
      return;
    }

    if (window.getComputedStyle(card).position === "static") {
      card.style.position = "relative";
    }
    card.style.cursor = "pointer";

    var link = document.createElement("a");
    link.className = "display-audit-card-link";
    link.href = "./display-audit-dashboard.html";
    link.title = "打开陈列稽核看板";
    link.setAttribute("aria-label", "打开陈列稽核看板");
    link.style.position = "absolute";
    link.style.inset = "0";
    link.style.zIndex = "100";
    link.style.display = "block";
    link.style.borderRadius = "inherit";
    link.style.background = "transparent";
    link.style.fontSize = "0";

    card.appendChild(link);
  }

  function bindDisplayAuditCard() {
    var cards = document.querySelectorAll(".top-kpi-row .kc");
    Array.prototype.forEach.call(cards, addNavigationLink);
  }

  function openDisplayAudit(event) {
    var target = event.target;
    var card = target && target.closest
      ? target.closest(".top-kpi-row .kc")
      : null;

    if (!isDisplayAuditCard(card)) {
      return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();
    window.location.assign(
      new URL("display-audit-dashboard.html", window.location.href).href
    );
  }

  document.addEventListener("click", openDisplayAudit, true);

  function startObserver() {
    if (!document.body) return;
    new MutationObserver(bindDisplayAuditCard).observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      bindDisplayAuditCard();
      startObserver();
    });
  } else {
    bindDisplayAuditCard();
    startObserver();
  }
})();
