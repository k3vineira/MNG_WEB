/**
 * alertas.js - Módulo unificado de alertas y notificaciones Monagua.
 * Todas las alertas se gestionan a través del sistema Toast superior derecho con temporizador.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Si quedan elementos .alert residuales en el DOM, se cierran automáticamente o se muestran como Toast
    var legacyAlerts = document.querySelectorAll('.alert');
    legacyAlerts.forEach(function (alertEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
            setTimeout(function () {
                try {
                    var bsAlert = new bootstrap.Alert(alertEl);
                    bsAlert.close();
                } catch (e) {
                    alertEl.style.display = 'none';
                }
            }, 5000);
        }
    });
});
