document.addEventListener("DOMContentLoaded", function () {
    /* Fecha */
    const currentDateEl = document.getElementById('currentDate');
    if (currentDateEl) {
        currentDateEl.textContent = new Date().toLocaleDateString('es-CO', { weekday:'short', year:'numeric', month:'short', day:'numeric' });
    }

    const C = { green:'#198754', amber:'#ffc107', rose:'#dc3545', gray:'#f0f0f0' };

    const ctx = document.getElementById('chartEstado');
    if (ctx) {
        const reservasConf = parseInt(ctx.getAttribute('data-conf'), 10) || 0;
        const reservasPend = parseInt(ctx.getAttribute('data-pend'), 10) || 0;
        const reservasCan  = parseInt(ctx.getAttribute('data-can'), 10) || 0;

        const tot = reservasConf + reservasPend + reservasCan;
        new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Confirmadas','Pendientes','Canceladas'],
            datasets: [{
              data: tot > 0 ? [reservasConf, reservasPend, reservasCan] : [1],
              backgroundColor: tot > 0 ? [C.green, C.amber, C.rose] : ['#e5e7eb'],
              borderWidth: 0,
              hoverOffset: tot > 0 ? 8 : 0
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
              legend: { display: false },
              tooltip: {
                enabled: tot > 0,
                callbacks: {
                  label: c => ' ' + c.label + ': ' + c.parsed + ' reservas'
                }
              }
            }
          }
        });
    }
});
