document.addEventListener('DOMContentLoaded', function() {
    const config = {
        locale: 'es',
        dateFormat: 'Y-m-d',
        allowInput: true
    };
    
    const inicioInput = document.getElementById('id_fecha_inicio');
    const finInput = document.getElementById('id_fecha_fin');
    
    if (inicioInput) flatpickr(inicioInput, config);
    if (finInput) flatpickr(finInput, config);
});
