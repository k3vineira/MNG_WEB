document.addEventListener("DOMContentLoaded", function () {

    const dateInput = document.getElementById('fecha_input');

    if (dateInput) {
        // 1. Obtener la fecha de hoy y sumar 5 días exactos
        const hoy = new Date();
        const fechaMinima = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() + 5);

        // 2. Formatear como YYYY-MM-DD (Ejemplo: "2026-09-12")
        const yyyy = fechaMinima.getFullYear();
        const mm = String(fechaMinima.getMonth() + 1).padStart(2, '0');
        const dd = String(fechaMinima.getDate()).padStart(2, '0');
        const fechaMinimaTexto = `${yyyy}-${mm}-${dd}`;

        // 3. Inicializar Flatpickr con la fecha mínima exacta
        flatpickr(dateInput, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            minDate: fechaMinimaTexto, // Bloquea del 7 al 11 de septiembre
            disableMobile: true,
            onChange: function () {
                if (typeof window.updatePrice === 'function') {
                    window.updatePrice();
                }
            }
        });
    }
    // 2. CÁLCULO DE PRECIOS Y CONTADORES
    window.updatePrice = function () {
        const fechaInput = document.getElementById('fecha_input');
        const displayTotal = document.getElementById('total_reserva_display');
        const submitBtn = document.getElementById('submit_reserva_btn');

        if (!fechaInput || !displayTotal) return;

        const fecha = fechaInput.value;
        const adultos = parseInt(document.getElementById('adultos_input')?.value) || 0;
        const menores = parseInt(document.getElementById('menores_input')?.value) || 0;

        if (!fecha) {
            displayTotal.innerHTML = `<small class="text-muted">Selecciona una fecha para ver el precio.</small>`;
            return;
        }

        let precio_adulto = 0;
        let precio_menor = 0;
        let tarifa_encontrada = false;

        const elementosTarifas = document.querySelectorAll('.tarifa-item');

        for (let el of elementosTarifas) {
            const fechaInicio = el.getAttribute('data-inicio');
            const fechaFin = el.getAttribute('data-fin');

            if (fecha >= fechaInicio && fecha <= fechaFin) {
                precio_adulto = parseFloat(el.getAttribute('data-adulto')) || 0;
                precio_menor = parseFloat(el.getAttribute('data-menor')) || 0;
                tarifa_encontrada = true;
                break;
            }
        }

        if (tarifa_encontrada) {
            const total = (adultos * precio_adulto) + (menores * precio_menor);
            displayTotal.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-secondary fw-semibold">Total estimado:</span>
                    <h4 class="text-success fw-bold mb-0">$${total.toLocaleString('es-CO')}</h4>
                </div>
            `;
            
            if (submitBtn && submitBtn.getAttribute('data-auth') === 'true') {
                submitBtn.disabled = false;
            }
        } else {
            displayTotal.innerHTML = `<small class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i>No hay tarifas disponibles para esta fecha.</small>`;
            if (submitBtn) submitBtn.disabled = true;
        }
    };

    window.updateCount = function (type, change) {
        const input = document.getElementById(type + '_input');
        const display = document.getElementById(type + '_count');
        const compatInput = document.getElementById('numero_personas_compat');

        if (!input || !display) return;

        let currentValue = parseInt(input.value) || 0;
        
        if (type === 'adultos' && currentValue + change < 1) return; 
        if (type === 'menores' && currentValue + change < 0) return; 
        if (currentValue + change > 20) return; 
        
        currentValue += change;
        input.value = currentValue;
        display.innerText = currentValue;

        if (compatInput) {
            const adultos = parseInt(document.getElementById('adultos_input')?.value) || 1;
            const menores = parseInt(document.getElementById('menores_input')?.value) || 0;
            compatInput.value = adultos + menores;
        }

        window.updatePrice();
    };

    window.updatePrice();
});