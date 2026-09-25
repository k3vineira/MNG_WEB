/**
 * ═════════════════════════════════════════════════════════════════════
 * MONAGUA SIDEBAR CONTROLLER (BOOTSTRAP INTEGRATION)
 * ═════════════════════════════════════════════════════════════════════
 */

// ── 1. Restauración Inmediata de Estado (Síncrona para evitar parpadeos) ──
(function () {
  try {
    var state = localStorage.getItem('monaguaSidebarState') || localStorage.getItem('sidebarState');
    if (state === 'slim') {
      document.body.classList.add('sidebar-slim-active');
    } else if (state === 'wide') {
      document.body.classList.remove('sidebar-slim-active');
    }
  } catch (err) {
    console.warn('Error leyendo estado de sidebar:', err);
  }
})();

// ── 2. Inicialización de Listeners y Tooltips ──
document.addEventListener('DOMContentLoaded', function () {
  function hideAllTooltips() {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) return;
    document.querySelectorAll('#mainSidebar [data-bs-toggle="tooltip"]').forEach(function (el) {
      var instance = bootstrap.Tooltip.getInstance(el);
      if (instance) {
        instance.hide();
      }
    });
  }

  // Alternar el sidebar (Slim ↔ Wide)
  function toggleSidebar(forceState) {
    var isCurrentlySlim = document.body.classList.contains('sidebar-slim-active');
    var targetSlim = typeof forceState === 'boolean' ? forceState : !isCurrentlySlim;

    hideAllTooltips();

    if (targetSlim) {
      document.body.classList.add('sidebar-slim-active');
      localStorage.setItem('monaguaSidebarState', 'slim');
      localStorage.setItem('sidebarState', 'slim');
    } else {
      document.body.classList.remove('sidebar-slim-active');
      localStorage.setItem('monaguaSidebarState', 'wide');
      localStorage.setItem('sidebarState', 'wide');
    }

    setTimeout(function () {
      window.dispatchEvent(new Event('resize'));
    }, 260);
  }

  // Desplegar el aside y abrir el apartado específico al hacer clic en icono contraído
  function expandAndOpenSection(targetSelector) {
    hideAllTooltips();

    // 1. Desplegar el aside
    document.body.classList.remove('sidebar-slim-active');
    localStorage.setItem('monaguaSidebarState', 'wide');
    localStorage.setItem('sidebarState', 'wide');

    // 2. Abrir el apartado correspondiente en la vista expandida
    if (targetSelector) {
      var targetEl = document.querySelector(targetSelector);
      if (targetEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
          var collapseInstance = bootstrap.Collapse.getOrCreateInstance(targetEl, { toggle: false });
          collapseInstance.show();
        } else {
          targetEl.classList.add('show');
        }

        var toggleBtn = document.querySelector('[data-bs-target="' + targetSelector + '"]');
        if (toggleBtn) {
          toggleBtn.classList.remove('collapsed');
          toggleBtn.setAttribute('aria-expanded', 'true');
        }
      }
    }

    setTimeout(function () {
      window.dispatchEvent(new Event('resize'));
    }, 260);
  }

  // Botones de alternancia manual
  document.querySelectorAll('.toggle-sidebar-btn, [data-sidebar-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleSidebar();
    });
  });

  // Iconos en modo slim que despliegan su apartado correspondiente
  document.querySelectorAll('[data-expand-sidebar-target]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var targetSelector = btn.getAttribute('data-expand-sidebar-target');
      expandAndOpenSection(targetSelector);
    });
  });

  // Tooltips de Bootstrap
  function initTooltips() {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) return;

    var tooltipElements = document.querySelectorAll(
      '#mainSidebar [data-bs-toggle="tooltip"]'
    );

    tooltipElements.forEach(function (el) {
      if (!bootstrap.Tooltip.getInstance(el)) {
        new bootstrap.Tooltip(el, {
          boundary: document.body,
          trigger: 'hover',
          placement: el.getAttribute('data-bs-placement') || 'right'
        });
      }
    });
  }

  // Ocultar tooltips al hacer clic en enlaces o botones
  document.querySelectorAll('#mainSidebar a, #mainSidebar button').forEach(function (el) {
    el.addEventListener('click', function () {
      hideAllTooltips();
    });
  });

  initTooltips();

  window.MonaguaSidebar = {
    toggle: toggleSidebar,
    expandAndOpen: expandAndOpenSection,
    setSlim: function () { toggleSidebar(true); },
    setWide: function () { toggleSidebar(false); }
  };
});
