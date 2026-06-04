document.addEventListener("DOMContentLoaded", function () {

    window.updatePrice = function() {
        const fecha = document.getElementById('fecha_input').value;
        const adultos = parseInt(document.getElementById('adultos_input').value) || 0;
        const menores = parseInt(document.getElementById('menores_input').value) || 0;
        
        const displayTotal = document.getElementById('total_reserva_display');
        const submitBtn = document.getElementById('submit_reserva_btn');

        if (!fecha) {
            displayTotal.innerHTML = `<small class="text-muted">Selecciona una fecha para ver el precio.</small>`;
            return;
        }

        let precio_adulto = 0;
        let precio_menor = 0;
        let tarifa_encontrada = false;

        // Leemos los elementos ocultos del HTML que tienen los datos de las tarifas
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
            
            if (submitBtn.getAttribute('data-auth') === 'true') {
                submitBtn.disabled = false;
            }
        } else {
            displayTotal.innerHTML = `<small class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i>No hay tarifas disponibles para esta fecha.</small>`;
            submitBtn.disabled = true;
        }
    };

    window.updateCount = function(type, change) {
        const input = document.getElementById(type + '_input');
        const display = document.getElementById(type + '_count');
        const compatInput = document.getElementById('numero_personas_compat');
        let currentValue = parseInt(input.value) || 0;
        
        if (type === 'adultos' && currentValue + change < 1) return; 
        if (type === 'menores' && currentValue + change < 0) return; 
        if (currentValue + change > 20) return; 
        
        currentValue += change;
        input.value = currentValue;
        display.innerText = currentValue;

        if (compatInput) {
            const adultos = parseInt(document.getElementById('adultos_input').value) || 1;
            const menores = parseInt(document.getElementById('menores_input').value) || 0;
            compatInput.value = adultos + menores;
        }

        window.updatePrice();
    };
});