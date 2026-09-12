document.addEventListener("DOMContentLoaded", function () {

    const dateInput = document.getElementById('fecha_input');

    if (dateInput) {
        // 1. Obtener la fecha de hoy y sumar 5 días exactos
        const hoy = new Date();
        const fechaMinima = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() + 5);

        // 2. Formatear como YYYY-MM-DD
        const yyyy = fechaMinima.getFullYear();
        const mm = String(fechaMinima.getMonth() + 1).padStart(2, '0');
        const dd = String(fechaMinima.getDate()).padStart(2, '0');
        const fechaMinimaTexto = `${yyyy}-${mm}-${dd}`;

        // 3. Inicializar Flatpickr con la fecha mínima exacta
        flatpickr(dateInput, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            minDate: fechaMinimaTexto,
            disableMobile: true,
            onChange: function () {
                if (typeof window.updatePrice === 'function') {
                    window.updatePrice();
                }
            },
            onValueUpdate: function () {
                if (typeof window.updatePrice === 'function') {
                    window.updatePrice();
                }
            },
            onClose: function () {
                if (typeof window.updatePrice === 'function') {
                    window.updatePrice();
                }
            }
        });

        dateInput.addEventListener('change', function () {
            if (typeof window.updatePrice === 'function') {
                window.updatePrice();
            }
        });

        dateInput.addEventListener('input', function () {
            if (typeof window.updatePrice === 'function') {
                window.updatePrice();
            }
        });
    }

    // 2. CÁLCULO DE PRECIOS Y CONTADORES
    window.updatePrice = function () {
        const fechaInput = document.getElementById('fecha_input');
        const displayTotal = document.getElementById('total_reserva_display');
        const submitBtn = document.getElementById('submit_reserva_btn');

        if (!displayTotal) return;

        const fecha = fechaInput ? fechaInput.value : '';
        const adultos = parseInt(document.getElementById('adultos_input')?.value) || 0;
        const menores = parseInt(document.getElementById('menores_input')?.value) || 0;

        if (!fecha) {
            displayTotal.innerHTML = `<small class="text-muted"><i class="bi bi-calendar3 me-1"></i>Selecciona una fecha para calcular el total.</small>`;
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

        // Si no encontró tarifa por rango de fecha exacto, tomar la primera disponible como fallback
        if (!tarifa_encontrada && elementosTarifas.length > 0) {
            const primeraTarifa = elementosTarifas[0];
            precio_adulto = parseFloat(primeraTarifa.getAttribute('data-adulto')) || 0;
            precio_menor = parseFloat(primeraTarifa.getAttribute('data-menor')) || 0;
            tarifa_encontrada = true;
        }

        if (tarifa_encontrada) {
            const base_total = (adultos * precio_adulto) + (menores * precio_menor);
            let total_final = base_total;
            let promo_aplicada = null;

            const elementosPromociones = document.querySelectorAll('.promocion-item');
            
            // 1. Buscar promoción vigente para la fecha elegida
            for (let el of elementosPromociones) {
                const pInicio = el.getAttribute('data-inicio');
                const pFin = el.getAttribute('data-fin');

                if (pInicio && pFin && fecha >= pInicio && fecha <= pFin) {
                    const porcentaje = parseFloat(el.getAttribute('data-porcentaje')) || 0;
                    const valAdulto = parseFloat(el.getAttribute('data-val-adulto')) || 0;
                    const valMenor = parseFloat(el.getAttribute('data-val-menor')) || 0;

                    let promoAdulto = (valAdulto > 0) ? valAdulto : (porcentaje > 0 ? (precio_adulto * (1 - (porcentaje / 100))) : precio_adulto);
                    let promoMenor = (valMenor > 0) ? valMenor : (porcentaje > 0 ? (precio_menor * (1 - (porcentaje / 100))) : precio_menor);

                    total_final = Math.round((adultos * promoAdulto) + (menores * promoMenor));
                    const ahorro = base_total - total_final;

                    if (ahorro > 0) {
                        promo_aplicada = {
                            nombre: el.getAttribute('data-nombre') || 'Promoción Especial',
                            porcentaje: porcentaje > 0 ? porcentaje : Math.round((ahorro / base_total) * 100),
                            descuentoMonto: ahorro
                        };
                    }
                    break;
                }
            }

            // 2. Si no hubo coincidencia por fecha estricta, aplicar la promoción asignada al paquete
            if (!promo_aplicada && elementosPromociones.length > 0) {
                const promoEl = elementosPromociones[0];
                const porcentaje = parseFloat(promoEl.getAttribute('data-porcentaje')) || 0;
                const valAdulto = parseFloat(promoEl.getAttribute('data-val-adulto')) || 0;
                const valMenor = parseFloat(promoEl.getAttribute('data-val-menor')) || 0;

                let promoAdulto = (valAdulto > 0) ? valAdulto : (porcentaje > 0 ? (precio_adulto * (1 - (porcentaje / 100))) : precio_adulto);
                let promoMenor = (valMenor > 0) ? valMenor : (porcentaje > 0 ? (precio_menor * (1 - (porcentaje / 100))) : precio_menor);

                total_final = Math.round((adultos * promoAdulto) + (menores * promoMenor));
                const ahorro = base_total - total_final;

                if (ahorro > 0) {
                    promo_aplicada = {
                        nombre: promoEl.getAttribute('data-nombre') || 'Promoción Especial',
                        porcentaje: porcentaje > 0 ? porcentaje : Math.round((ahorro / base_total) * 100),
                        descuentoMonto: ahorro
                    };
                }
            }

            if (promo_aplicada && promo_aplicada.descuentoMonto > 0) {
                displayTotal.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1 text-muted small">
                        <span>Total regular (${adultos} adulto${adultos > 1 ? 's' : ''}${menores > 0 ? ', ' + menores + ' menor' + (menores > 1 ? 'es' : '') : ''}):</span>
                        <span class="text-decoration-line-through fw-semibold">$${base_total.toLocaleString('es-CO')}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2 text-danger small">
                        <span><i class="bi bi-tag-fill me-1"></i>Descuento (${promo_aplicada.porcentaje}% OFF - ${promo_aplicada.nombre}):</span>
                        <span class="fw-bold">-$${promo_aplicada.descuentoMonto.toLocaleString('es-CO')}</span>
                    </div>
                    <hr class="my-2 border-secondary opacity-25">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-dark fw-bold" style="font-size: 1rem;">Total con Descuento:</span>
                        <h3 class="text-success fw-black mb-0" style="font-weight: 800; font-size: 1.65rem;">$${total_final.toLocaleString('es-CO')}</h3>
                    </div>
                `;
            } else {
                displayTotal.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-dark fw-bold" style="font-size: 1rem;">Total estimado:</span>
                        <h3 class="text-success fw-black mb-0" style="font-weight: 800; font-size: 1.65rem;">$${total_final.toLocaleString('es-CO')}</h3>
                    </div>
                `;
            }

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

});