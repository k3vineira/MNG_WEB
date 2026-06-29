/**
 * Sidebar Dual (Wide / Slim) - Estado y persistencia con localStorage
 * Compatible con Bootstrap 5 collapse events
 */

// ── Restauración inmediata del estado (antes del DOMContentLoaded) ──
// Se ejecuta síncronamente para evitar el parpadeo del sidebar ancho
(function () {
  var state = localStorage.getItem('sidebarState');
  if (state === 'slim') {
    // IDs posibles según el rol: admin, guía o turista
    var wideIds = ['sidebarWide', 'sidebarGuiaWide', 'sidebarTuristaWide'];
    var slimIds = ['sidebarSlim', 'sidebarGuiaSlim', 'sidebarTuristaSlim'];

    wideIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.classList.remove('show');
    });
    slimIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.classList.add('show');
    });
    document.body.classList.add('sidebar-slim-active');
  }
})();

// ── Listeners de Bootstrap Collapse para persistir el estado ──
document.addEventListener('DOMContentLoaded', function () {
  // IDs de la vista expandida según el rol
  var wideIds = ['sidebarWide', 'sidebarGuiaWide', 'sidebarTuristaWide'];

  wideIds.forEach(function (id) {
    var wideElement = document.getElementById(id);
    if (wideElement) {
      wideElement.addEventListener('hide.bs.collapse', function () {
        document.body.classList.add('sidebar-slim-active');
        localStorage.setItem('sidebarState', 'slim');
      });
      wideElement.addEventListener('show.bs.collapse', function () {
        document.body.classList.remove('sidebar-slim-active');
        localStorage.setItem('sidebarState', 'wide');
      });
    }
  });
});
