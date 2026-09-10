/* Formateador COP */
const formatCOP = v => 'COP $' + Math.round(v).toLocaleString('es-CO');

/* Calcula un paso de escala limpio basado en el máximo real */
function calcStepSize(data) {
  const max = Math.max(...data, 180); /* mínimo 180 para que no quede vacío */
  const raw = max / 5;
  const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = Math.ceil(raw / magnitude) * magnitude;
  return step;
}

document.addEventListener('DOMContentLoaded', function() {
    /* Fecha */
    const dateElement = document.getElementById('currentDate');
    if (dateElement) {
        dateElement.textContent = new Date().toLocaleDateString('es-CO', { weekday:'short', year:'numeric', month:'short', day:'numeric' });
    }

    const C = { green:'#1a261f', greenLight:'rgba(26,38,31,.12)', amber:'#f59e0b', rose:'#dc3545', gray:'#f0f0f0', muted:'#aaa' };

    /* Gráfica 1 — Ingresos mensuales */
    if (document.getElementById('chartIngresos') && typeof ingresosData !== 'undefined') {
        const stepIngresos = calcStepSize(ingresosData);
        const maxIngresos  = stepIngresos * 6; /* 6 pasos arriba del máximo */

        new Chart(document.getElementById('chartIngresos'), {
          type: 'line',
          data: {
            labels: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
            datasets: [{
              label: 'Ingresos (COP $)',
              data: ingresosData,
              borderColor: C.green,
              backgroundColor: C.greenLight,
              borderWidth: 2.5,
              tension: .4,
              fill: true,
              pointBackgroundColor: C.green,
              pointRadius: 4,
              pointHoverRadius: 7
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: c => ' ' + formatCOP(c.parsed.y)
                }
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { font: { size: 11 }, color: C.muted }
              },
              y: {
                min: 0,
                max: maxIngresos,
                grid: { color: C.gray },
                ticks: {
                  stepSize: stepIngresos,
                  font: { size: 11 },
                  color: C.muted,
                  callback: v => formatCOP(v)
                }
              }
            }
          }
        });
    }

    /* Gráfica 2 — Estado reservas (donut) */
    if (document.getElementById('chartEstado') && typeof reservasConf !== 'undefined') {
        const tot = reservasConf + reservasPend + reservasCan;
        new Chart(document.getElementById('chartEstado'), {
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

    /* Gráfica 3 — Reservas esta semana */
    if (document.getElementById('chartSemana') && typeof dataSemana !== 'undefined') {
        const maxS = Math.max(...dataSemana) || 1;
        new Chart(document.getElementById('chartSemana'), {
          type: 'bar',
          data: {
            labels: ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'],
            datasets: [{
              label: 'Reservas',
              data: dataSemana,
              backgroundColor: dataSemana.map(v => v === maxS && v > 0 ? C.green : C.greenLight),
              borderRadius: 6,
              borderSkipped: false
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: c => ' ' + c.parsed.y + ' reservas'
                }
              }
            },
            scales: {
              x: {
                grid: { display: false },
                ticks: { font: { size: 11 }, color: C.muted }
              },
              y: {
                display: false,
                min: 0
              }
            }
          }
        });
    }

    /* Exportar PDF */
    const btnExportPdf = document.getElementById('btnExportPdf');
    if (btnExportPdf) {
        btnExportPdf.addEventListener('click', async function () {
          const btn = this;
          btn.disabled = true;
          btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generando…';
          try {
            const target = document.getElementById('mainContent') || document.body;
            const canvas = await html2canvas(target, {
              scale: 2, useCORS: true, backgroundColor: '#f8f9fa',
              logging: false, scrollY: -window.scrollY,
              windowWidth: target.scrollWidth, windowHeight: target.scrollHeight
            });
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
            const pW = pdf.internal.pageSize.getWidth();
            const pH = pdf.internal.pageSize.getHeight();
            const ratio = pW / canvas.width;
            const totalH = canvas.height * ratio;
            let posY = 0, pg = 1;
            const totalPages = Math.ceil(totalH / pH);
            let loopLimit = 0;

            const header = (n, t) => {
              pdf.setFillColor(33, 37, 41); pdf.rect(0, 0, pW, 10, 'F');
              pdf.setTextColor(255, 255, 255); pdf.setFontSize(8); pdf.setFont('helvetica', 'bold');
              pdf.text('MONAGUA — Tablero de Rendimiento', 8, 6.5);
              pdf.text('Generado: ' + new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' }) + '   Pág ' + n + '/' + t, pW - 8, 6.5, { align: 'right' });
            };

            while (posY < totalH - 1 && loopLimit < 50) {
              if (pg > 1) pdf.addPage();
              header(pg, totalPages);
              const sliceH = Math.min(pH - 10, totalH - posY);
              if (sliceH <= 0) break;
              const sc = document.createElement('canvas');
              sc.width = canvas.width;
              sc.height = Math.round(sliceH / ratio);
              sc.getContext('2d').drawImage(canvas, 0, Math.round(posY / ratio), canvas.width, sc.height, 0, 0, sc.width, sc.height);
              pdf.addImage(sc.toDataURL('image/jpeg', .92), 'JPEG', 0, 10, pW, sliceH);
              posY += sliceH; pg++; loopLimit++;
            }
            pdf.save('monagua-dashboard-' + new Date().toISOString().slice(0, 10) + '.pdf');
          } catch (e) {
            console.error(e);
            if (typeof window.mostrarToast === 'function') {
              window.mostrarToast('error', 'Error en Exportación', 'Ocurrió un error al generar el archivo PDF.', 5000);
            }
          } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-file-earmark-pdf-fill"></i> Exportar PDF';
          }
        });
    }
});
