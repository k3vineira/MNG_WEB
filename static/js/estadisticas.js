document.addEventListener("DOMContentLoaded", function () {
    if (typeof Chart === 'undefined') {
        console.error("Chart.js no está cargado.");
        return;
    }

    Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
    Chart.defaults.color = "#6c757d";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;

    const formatCOP = (v) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(v);
    };
    const abbreviateCOP = (v) => {
        if (v >= 1000000) {
            return "COP $" + (v / 1000000).toFixed(1) + "M";
        } else if (v >= 1000) {
            return "COP $" + (v / 1000).toFixed(0) + "K";
        }
        return "COP $" + v;
    };

    Chart.defaults.interaction = {
        mode: 'index',
        intersect: false,
    };

    Chart.defaults.plugins.tooltip = {
        intersect: false,
        callbacks: {
            label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                    label += ': ';
                }
                if (context.parsed.y !== null) {
                    if (context.dataset.label && context.dataset.label.includes("Inversión")) {
                        label += formatCOP(context.parsed.y);
                    } else {
                        label += context.parsed.y;
                    }
                }
                return label;
            }
        }
    };

    // Obtenemos los datos desde el contenedor HTML
    const container = document.getElementById('estadisticas-data-container');
    if (!container) {
        console.error("No se encontró el contenedor de datos de estadísticas.");
        return;
    }

    const safeParse = (key, defaultVal) => {
        try {
            const val = container.getAttribute(key);
            if (!val) return defaultVal;
            // Si el valor no es un string válido JSON pero es un número, parseFloat funcionaría.
            // JSON.parse maneja arrays "[]" y números "5" correctamente.
            return JSON.parse(val);
        } catch(e) {
            return defaultVal;
        }
    };

    const mesesLabels = safeParse('data-meses-labels', []);
    const mesesDatos = safeParse('data-meses-datos', []);
    const mesesInversion = safeParse('data-meses-inversion', []);
    const aniosLabels = safeParse('data-anios-labels', []);
    const aniosDatos = safeParse('data-anios-datos', []);
    const aniosReservas = safeParse('data-anios-reservas', []);
    const aniosCanceladas = safeParse('data-anios-canceladas', []);
    const diasDatos = safeParse('data-dias-datos', []);
    
    // Estos pueden venir sin comillas, JSON.parse lo leerá como números.
    const pqrsAbiertas = safeParse('data-pqrs-abiertas', 0);
    const pqrsGestion = safeParse('data-pqrs-gestion', 0);
    const pqrsCerradas = safeParse('data-pqrs-cerradas', 0);
    const reservasConf = safeParse('data-reservas-conf', 0);
    const reservasPend = safeParse('data-reservas-pend', 0);
    const reservasCan = safeParse('data-reservas-can', 0);
    const reservasComp = safeParse('data-reservas-comp', 0);
    
    const destinosLabels = safeParse('data-destinos-labels', []);
    const destinosDatos = safeParse('data-destinos-datos', []);
    const radarDatosArray = safeParse('data-radar-datos', []);

    // Colores reutilizables
    const rootStyle = getComputedStyle(document.documentElement);
    const C = {
        blue: rootStyle.getPropertyValue('--estadisticas-blue').trim() || "#2563eb",
        green: rootStyle.getPropertyValue('--estadisticas-green').trim() || "#10b981",
        yellow: rootStyle.getPropertyValue('--estadisticas-yellow').trim() || "#f59e0b",
        red: rootStyle.getPropertyValue('--estadisticas-red').trim() || "#ef4444",
        cyan: rootStyle.getPropertyValue('--estadisticas-cyan').trim() || "#06b6d4",
        purple: rootStyle.getPropertyValue('--estadisticas-purple').trim() || "#8b5cf6",
        orange: rootStyle.getPropertyValue('--estadisticas-orange').trim() || "#f97316",
        pink: rootStyle.getPropertyValue('--estadisticas-pink').trim() || "#ec4899",
        teal: rootStyle.getPropertyValue('--estadisticas-teal').trim() || "#14b8a6",
        gridLine: rootStyle.getPropertyValue('--estadisticas-grid-line').trim() || "#f1f5f9",
    };

    function alphaColor(hex, a) {
        const hexNormalized = hex.startsWith('#') ? hex : '#2563eb';
        const r = parseInt(hexNormalized.slice(1, 3), 16) || 0;
        const g = parseInt(hexNormalized.slice(3, 5), 16) || 0;
        const b = parseInt(hexNormalized.slice(5, 7), 16) || 0;
        return `rgba(${r},${g},${b},${a})`;
    }

    // 1. Evolución Mensual
    const chartEvolucionMensual = document.getElementById("chartEvolucionMensual");
    if (chartEvolucionMensual && mesesLabels.length > 0) {
        new Chart(chartEvolucionMensual, {
            type: "line",
            data: {
                labels: mesesLabels,
                datasets: [
                    {
                        label: "Reservas",
                        data: mesesDatos,
                        borderColor: C.blue,
                        backgroundColor: alphaColor(C.blue, 0.06),
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: C.blue,
                        yAxisID: "yReservas"
                    },
                    {
                        label: "Inversión (COP $)",
                        data: mesesInversion,
                        borderColor: C.green,
                        backgroundColor: alphaColor(C.green, 0.06),
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: C.green,
                        yAxisID: "yInversion"
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: "index", intersect: false },
                plugins: { legend: { position: "top" } },
                scales: {
                    yReservas: {
                        type: "linear",
                        position: "left",
                        grid: { color: C.gridLine },
                        ticks: { stepSize: 1 }
                    },
                    yInversion: {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        ticks: {
                            callback: v => abbreviateCOP(v)
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. Estados de Reserva
    const chartEstadosPie = document.getElementById("chartEstadosPie");
    if (chartEstadosPie) {
        new Chart(chartEstadosPie, {
            type: "doughnut",
            data: {
                labels: ["Confirmadas", "Pendientes", "Canceladas", "Completadas"],
                datasets: [{
                    data: [reservasConf, reservasPend, reservasCan, reservasComp],
                    backgroundColor: [C.green, C.yellow, C.red, C.blue],
                    borderWidth: 4,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                cutout: "72%",
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } }
                }
            }
        });
    }

    // 3. Inversión Anual
    const chartInversionAnual = document.getElementById("chartInversionAnual");
    if (chartInversionAnual && aniosLabels.length > 0) {
        new Chart(chartInversionAnual, {
            type: "bar",
            data: {
                labels: aniosLabels,
                datasets: [{
                    label: "Inversión (COP $)",
                    data: aniosDatos,
                    backgroundColor: C.yellow,
                    borderRadius: 8,
                    barThickness: 36
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        grid: { color: C.gridLine },
                        beginAtZero: true,
                        ticks: { callback: v => abbreviateCOP(v) }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 4. Días de la Semana
    const chartDiasSemana = document.getElementById("chartDiasSemana");
    if (chartDiasSemana && diasDatos.length > 0) {
        new Chart(chartDiasSemana, {
            type: "bar",
            data: {
                labels: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                datasets: [{
                    label: "Solicitudes",
                    data: diasDatos,
                    backgroundColor: C.cyan,
                    borderRadius: 6,
                    barThickness: 14
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: C.gridLine }, beginAtZero: true },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    // 5. PQRS Estados
    const chartPqrsEstados = document.getElementById("chartPqrsEstados");
    if (chartPqrsEstados) {
        new Chart(chartPqrsEstados, {
            type: "polarArea",
            data: {
                labels: ["Abiertas", "En Gestión", "Resueltas"],
                datasets: [{
                    data: [pqrsAbiertas, pqrsGestion, pqrsCerradas],
                    backgroundColor: [
                        alphaColor(C.blue, 0.7),
                        alphaColor(C.yellow, 0.7),
                        alphaColor(C.green, 0.7)
                    ],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } }
            }
        });
    }

    // 6. Comparativa Anual
    const chartComparativaAnual = document.getElementById("chartComparativaAnual");
    if (chartComparativaAnual && aniosLabels.length > 0) {
        new Chart(chartComparativaAnual, {
            type: "bar",
            data: {
                labels: aniosLabels,
                datasets: [
                    {
                        label: "Total Reservas",
                        data: aniosReservas,
                        backgroundColor: alphaColor(C.blue, 0.8),
                        borderRadius: 6,
                        barThickness: 24
                    },
                    {
                        label: "Cancelaciones",
                        data: aniosCanceladas,
                        backgroundColor: alphaColor(C.red, 0.75),
                        borderRadius: 6,
                        barThickness: 24
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "top" } },
                scales: {
                    y: { grid: { color: C.gridLine }, beginAtZero: true },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 7. Top Destinos
    const chartTopDestinos = document.getElementById("chartTopDestinos");
    if (chartTopDestinos && destinosLabels.length > 0) {
        new Chart(chartTopDestinos, {
            type: "bar",
            data: {
                labels: destinosLabels,
                datasets: [{
                    label: "Reservas",
                    data: destinosDatos,
                    backgroundColor: [
                        alphaColor(C.green, 0.85),
                        alphaColor(C.blue, 0.75),
                        alphaColor(C.cyan, 0.8),
                        alphaColor(C.orange, 0.75),
                        alphaColor(C.purple, 0.7)
                    ],
                    borderRadius: 6,
                    barThickness: 16
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: C.gridLine }, beginAtZero: true },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    // 8. Radar Perfil del Viajero
    const chartRadarPerfil = document.getElementById("chartRadarPerfil");
    if (chartRadarPerfil && radarDatosArray.length > 0) {
        new Chart(chartRadarPerfil, {
            type: "radar",
            data: {
                labels: ["Reservas", "Inversión", "Fidelidad", "Calificaciones", "PQRS resueltas", "Destinos"],
                datasets: [{
                    label: "Tu perfil",
                    data: radarDatosArray,
                    borderColor: C.green,
                    backgroundColor: alphaColor(C.green, 0.15),
                    borderWidth: 2,
                    pointBackgroundColor: C.green,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { stepSize: 20, font: { size: 10 } },
                        grid: { color: C.gridLine },
                        pointLabels: { font: { size: 11 } }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 9. Inversión Acumulada Mensual
    const chartInversionAcumulada = document.getElementById("chartInversionAcumulada");
    if (chartInversionAcumulada && mesesLabels.length > 0) {
        const acumulados = mesesInversion.reduce((acc, val, i) => {
            acc.push(i === 0 ? val : acc[i - 1] + val);
            return acc;
        }, []);

        new Chart(chartInversionAcumulada, {
            type: "line",
            data: {
                labels: mesesLabels,
                datasets: [{
                    label: "Inversión Acumulada (COP $)",
                    data: acumulados,
                    borderColor: C.cyan,
                    backgroundColor: alphaColor(C.cyan, 0.12),
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: C.cyan
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        grid: { color: C.gridLine },
                        beginAtZero: true,
                        ticks: { callback: v => abbreviateCOP(v) }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }
});

// Navegación de paneles para las tarjetas superiores
function navegarPanel(panelId, colorClass) {
    const targetBtn = document.querySelector(`[data-bs-target='${panelId}']`);
    if (targetBtn) {
        targetBtn.click();
        const tabContainer = document.getElementById('vistasMatrizTab');
        if (tabContainer) {
            tabContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        const bgClass = `bg-${colorClass}`;
        const bgSoftClass = `bg-${colorClass}-soft`;
        
        targetBtn.classList.add(bgClass, 'text-white', 'shadow');
        setTimeout(() => {
            targetBtn.classList.remove(bgClass, 'text-white', 'shadow');
            targetBtn.style.transition = "all 0.5s";
        }, 1500);
        
        const panelEl = document.querySelector(panelId);
        if(panelEl) {
            panelEl.classList.add(bgSoftClass);
            setTimeout(() => {
                panelEl.classList.remove(bgSoftClass);
                panelEl.style.transition = "background-color 0.5s";
            }, 1500);
        }
    }
}
