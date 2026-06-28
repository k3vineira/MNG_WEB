/**
 * alertas.js - Auto-cierre de alertas de Bootstrap después de 5 segundos.
 * Cierra automáticamente las alertas informativas (no las de error crítico).
 */

document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        var alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function (alert) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 5000);
});
