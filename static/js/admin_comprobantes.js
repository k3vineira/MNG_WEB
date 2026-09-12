// Búsqueda en vivo
document.addEventListener('DOMContentLoaded', function() {
    const buscarInput = document.getElementById('buscarComprobante');
    if (buscarInput) {
        buscarInput.addEventListener('input', function () {
            var q = this.value.toLowerCase().trim();
            document.querySelectorAll('.comp-row').forEach(function (row) {
                var texto = row.getAttribute('data-buscar') || '';
                row.style.display = texto.includes(q) ? '' : 'none';
            });
        });
    }
});
