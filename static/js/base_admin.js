(function () {
  const btn = document.getElementById("sidebar-toggle");
  const sb = document.getElementById("mainSidebar");
  const ov = document.getElementById("sidebar-overlay");
  const content = document.getElementById("mainContent");

  const ICON_OPEN = '<i class="bi bi-list fs-5"></i>';
  const ICON_CLOSE = '<i class="bi bi-x-lg fs-5"></i>';

  function toggleSidebar(forceClose = false) {
    const isOpen = document.body.classList.contains("sidebar-open");
    if (isOpen || forceClose) {
      document.body.classList.remove("sidebar-open");
      btn.innerHTML = ICON_OPEN;
      btn.setAttribute("aria-expanded", "false");
    } else {
      document.body.classList.add("sidebar-open");
      btn.innerHTML = ICON_CLOSE;
      btn.setAttribute("aria-expanded", "true");
    }
  }

  if (btn && ov) {
    btn.addEventListener("click", () => toggleSidebar());
    ov.addEventListener("click", () => toggleSidebar(true));
  }

  if (sb) {
    sb.querySelectorAll('a, button[data-bs-toggle="dropdown"]').forEach(
      (link) => {
        link.addEventListener("click", (e) => {
          if (
            window.innerWidth < 992 &&
            link.tagName === "A" &&
            !link.hasAttribute("data-bs-toggle")
          ) {
            toggleSidebar(true);
          }
        });
      },
    );
  }
})();

(function () {
  function initTooltips() {
    if (typeof bootstrap === "undefined") return;
    var tooltipTriggerList = [].slice.call(
      document.querySelectorAll(
        '[data-bs-toggle="tooltip"], [title]:not([title=""])',
      ),
    );
    tooltipTriggerList.forEach(function (el) {
      var toggle = el.getAttribute("data-bs-toggle");
      if (toggle && toggle !== "tooltip") return;
      try {
        if (!bootstrap.Tooltip.getInstance(el)) {
          new bootstrap.Tooltip(el, {
            boundary: document.body,
            trigger: "hover",
          });
        }
      } catch (e) {}
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTooltips);
  } else {
    initTooltips();
  }
})();
