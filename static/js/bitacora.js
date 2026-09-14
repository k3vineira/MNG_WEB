  (function () {
    // Configuración de tipos y colores
    const CONFIG_TOAST = {
      success: {
        titulo: '¡Operación Exitosa!',
        colorTexto: '#1e4a2a',
        colorFondoIcono: 'rgba(44, 110, 60, 0.12)',
        colorIcono: '#2c6e3c',
        icono: 'bi-check-circle-fill',
        colorBarra: '#2c6e3c'
      },
      error: {
        titulo: '¡Atención - Error!',
        colorTexto: '#991b1b',
        colorFondoIcono: 'rgba(220, 53, 69, 0.12)',
        colorIcono: '#dc3545',
        icono: 'bi-exclamation-octagon-fill',
        colorBarra: '#dc3545'
      },
      danger: {
        titulo: '¡Atención - Error!',
        colorTexto: '#991b1b',
        colorFondoIcono: 'rgba(220, 53, 69, 0.12)',
        colorIcono: '#dc3545',
        icono: 'bi-exclamation-octagon-fill',
        colorBarra: '#dc3545'
      },
      warning: {
        titulo: '¡Advertencia!',
        colorTexto: '#92400e',
        colorFondoIcono: 'rgba(245, 158, 11, 0.14)',
        colorIcono: '#d97706',
        icono: 'bi-exclamation-triangle-fill',
        colorBarra: '#f59e0b'
      },
      info: {
        titulo: 'Notificación del Sistema',
        colorTexto: '#075985',
        colorFondoIcono: 'rgba(2, 132, 199, 0.12)',
        colorIcono: '#0284c7',
        icono: 'bi-info-circle-fill',
        colorBarra: '#0284c7'
      },
      offline: {
        titulo: 'Sin conexión',
        colorTexto: '#991b1b',
        colorFondoIcono: 'rgba(220, 53, 69, 0.12)',
        colorIcono: '#dc3545',
        icono: 'bi-wifi-off',
        colorBarra: '#dc3545'
      },
      online: {
        titulo: 'Conexión restablecida',
        colorTexto: '#1e4a2a',
        colorFondoIcono: 'rgba(44, 110, 60, 0.12)',
        colorIcono: '#2c6e3c',
        icono: 'bi-wifi',
        colorBarra: '#2c6e3c'
      }
    };

    /**
     * Función global para crear y disparar un Toast superior derecho con temporizador
     * @param {string} tipo - 'success', 'error', 'warning', 'info', 'offline', 'online'
     * @param {string} titulo - Título opcional (si no se pasa, toma el por defecto)
     * @param {string} mensaje - Mensaje descriptivo de la alerta
     * @param {number} duracion - Duración en milisegundos (por defecto 5000)
     */
    window.mostrarToast = function (tipo, titulo, mensaje, duracion) {
      duracion = duracion || 5000;
      tipo = (tipo || 'info').toLowerCase();
      if (!CONFIG_TOAST[tipo]) tipo = 'info';

      const conf = CONFIG_TOAST[tipo];
      const tituloFinal = titulo || conf.titulo;
      const mensajeFinal = mensaje || '';

      // Obtener o crear contenedor
      let container = document.getElementById('monaguaToastContainer');
      if (!container) {
        container = document.createElement('div');
        container.id = 'monaguaToastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.cssText = 'z-index: 99999; max-width: 400px; width: 100%; pointer-events: none;';
        document.body.appendChild(container);
      }

      // Crear elemento Toast
      const toastEl = document.createElement('div');
      toastEl.className = 'toast monagua-toast-item border-0 shadow-lg mb-3';
      toastEl.setAttribute('role', 'alert');
      toastEl.setAttribute('aria-live', 'assertive');
      toastEl.setAttribute('aria-atomic', 'true');
      toastEl.style.cssText = 'pointer-events: auto; border-radius: 16px; overflow: hidden; background: rgba(255, 255, 255, 0.97); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(0, 0, 0, 0.07);';

      toastEl.innerHTML = `
        <div class="d-flex align-items-center p-3">
          <div class="me-3 d-flex align-items-center justify-content-center rounded-circle flex-shrink-0" style="width: 42px; height: 42px; background-color: ${conf.colorFondoIcono}; color: ${conf.colorIcono};">
            <i class="bi ${conf.icono} fs-5"></i>
          </div>
          <div class="flex-grow-1 text-dark pe-2">
            <div class="fw-bold mb-0 text-start" style="font-size: 0.95rem; color: ${conf.colorTexto};">${tituloFinal}</div>
            <div class="small text-secondary mt-1 text-start" style="line-height: 1.35; font-size: 0.85rem;">${mensajeFinal}</div>
          </div>
          <button type="button" class="btn-close ms-auto align-self-start" data-bs-dismiss="toast" aria-label="Cerrar" style="font-size: 0.75rem;"></button>
        </div>
        <div class="toast-progress-track" style="height: 4px; width: 100%; background: rgba(0, 0, 0, 0.05); overflow: hidden;">
          <div class="toast-progress-bar" style="height: 100%; width: 100%; animation: monaguaToastTimer ${duracion}ms linear forwards; background-color: ${conf.colorBarra};"></div>
        </div>
      `;

      container.appendChild(toastEl);

      if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const bsToast = new bootstrap.Toast(toastEl, {
          autohide: true,
          delay: duracion
        });

        toastEl.addEventListener('hidden.bs.toast', function () {
          toastEl.remove();
        });

        bsToast.show();
      } else {
        // Fallback básico si Bootstrap JS no ha cargado
        toastEl.classList.add('show');
        setTimeout(function () {
          toastEl.remove();
        }, duracion);
      }
    };

    // Inicializar los Toasts renderizados desde Django al cargar el DOM
    document.addEventListener('DOMContentLoaded', function () {
      const serverToasts = document.querySelectorAll('#monaguaToastContainer .toast');
      serverToasts.forEach(function (toastEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
          const bsToast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 5000
          });
          toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
          });
          bsToast.show();
        }
      });

      // Monitoreo del estado de la conexión a Internet usando el diseño de Bitácora
      window.addEventListener('offline', function () {
        window.mostrarToast('offline', 'Sin conexión', 'En este momento no tienes conexión.', 6000);
      });

      window.addEventListener('online', function () {
        window.mostrarToast('online', 'Conexión restablecida', 'Se restauró la conexión a internet.', 5000);
      });
    });
  })();
