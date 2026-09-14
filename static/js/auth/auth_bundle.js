/**
 * alertas.js - Módulo unificado de alertas y notificaciones Monagua.
 * Todas las alertas se gestionan a través del sistema Toast superior derecho con temporizador.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Si quedan elementos .alert residuales en el DOM, se cierran automáticamente o se muestran como Toast
    var legacyAlerts = document.querySelectorAll('.alert');
    legacyAlerts.forEach(function (alertEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
            setTimeout(function () {
                try {
                    var bsAlert = new bootstrap.Alert(alertEl);
                    bsAlert.close();
                } catch (e) {
                    alertEl.style.display = 'none';
                }
            }, 5000);
        }
    });
});
/**
 * validar_passwords.js - Validación de coincidencia de contraseñas.
 * Compara los campos pass1 y pass2 antes de enviar el formulario.
 * Dispara la notificación Toast unificada superior derecha en caso de error.
 */

document.addEventListener('DOMContentLoaded', function () {
    var formRegistro = document.getElementById('formularioRegistro');
    var formReset = document.getElementById('form_reset');

    function validatePasswordMatch(event, btn) {
        var pass1 = document.getElementById('pass1');
        var pass2 = document.getElementById('pass2');

        if (pass1 && pass2) {
            if (pass1.value !== pass2.value) {
                event.preventDefault();
                pass2.classList.add('is-invalid');
                if (typeof window.mostrarToast === 'function') {
                    window.mostrarToast('error', 'Contraseñas no coinciden', 'Las contraseñas ingresadas no coinciden. Por favor verifícalas antes de continuar.', 5000);
                }
                pass2.focus();
            } else {
                pass2.classList.remove('is-invalid');
                if (btn) {
                    setTimeout(function() {
                        btn.disabled = true;
                    }, 0);
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Procesando...';
                }
            }
        }
    }

    if (formRegistro) {
        formRegistro.addEventListener('submit', function (event) {
            validatePasswordMatch(event, null);
        });
    }

    if (formReset) {
        var btnGuardar = document.getElementById('btn_guardar');
        formReset.addEventListener('submit', function (event) {
            validatePasswordMatch(event, btnGuardar);
        });
    }
});
/**
 * paises_ciudades.js - Manejo reactivo de selectores encadenados de ubicación
 * Basado en el dataset local dr5hn (País -> Departamento / Estado -> Ciudad / Municipio)
 * Compatible con registro.html, perfil_turista.html y vistas administrativas.
 */

document.addEventListener('DOMContentLoaded', function () {
  const selectPais = document.getElementById('id_pais');
  const selectDep = document.getElementById('id_departamento');
  const selectCiudad = document.getElementById('id_ciudad');

  // Si no existen en la página actual, salir de inmediato sin errores
  if (!selectPais || !selectDep || !selectCiudad) {
    return;
  }

  const API_PAISES = '/autenticacion/api/paises/';
  const API_DEPS = '/autenticacion/api/departamentos/';
  const API_CIUDADES = '/autenticacion/api/ciudades/';

  // Leer valores previos (data-prev) o valores seleccionados actualmente
  const prevPais = (selectPais.getAttribute('data-prev') || selectPais.value || '').trim();
  const prevDep = (selectDep.getAttribute('data-prev') || selectDep.value || '').trim();
  const prevCiudad = (selectCiudad.getAttribute('data-prev') || selectCiudad.value || '').trim();

  // Guardar estado inicial de deshabilitado (ej. perfil de solo lectura)
  const paisInitiallyDisabled = selectPais.hasAttribute('disabled');
  const depInitiallyDisabled = selectDep.hasAttribute('disabled') && !selectDep.classList.contains('form-select');
  const ciudadInitiallyDisabled = selectCiudad.hasAttribute('disabled') && !selectCiudad.classList.contains('form-select');

  /**
   * Helper: Limpia y deshabilita un select con un texto de placeholder
   */
  function resetSelect(selectEl, placeholderText, disable = true) {
    selectEl.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholderText;
    opt.selected = true;
    opt.disabled = true;
    selectEl.appendChild(opt);
    if (disable) {
      selectEl.disabled = true;
    }
  }

  /**
   * Helper: Muestra estado de carga en el select
   */
  function setLoading(selectEl, loadingText) {
    selectEl.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = loadingText;
    opt.selected = true;
    opt.disabled = true;
    selectEl.appendChild(opt);
    selectEl.disabled = true;
  }

  /**
   * Cargar Países desde el endpoint API local dr5hn
   */
  function cargarPaises() {
    setLoading(selectPais, 'Cargando países...');

    fetch(API_PAISES)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Error HTTP ' + response.status + ' al cargar países');
        }
        return response.json();
      })
      .then(function (paises) {
        selectPais.innerHTML = '';
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'Selecciona tu país...';
        defaultOpt.selected = true;
        defaultOpt.disabled = true;
        selectPais.appendChild(defaultOpt);

        let matchFound = false;

        paises.forEach(function (pais) {
          const opt = document.createElement('option');
          // Usar ISO3 (ej: COL) como valor principal, coincide con modelo CharField(max_length=3)
          opt.value = pais.iso3 || pais.iso2 || String(pais.id);
          opt.dataset.id = pais.id;
          opt.dataset.iso2 = pais.iso2 || '';
          opt.dataset.iso3 = pais.iso3 || '';

          const flag = pais.emoji ? pais.emoji + ' ' : '';
          opt.textContent = flag + pais.name;

          // Comprobar coincidencia con prevPais (por iso3, iso2 o id)
          if (
            prevPais &&
            (prevPais.toUpperCase() === (pais.iso3 || '').toUpperCase() ||
             prevPais.toUpperCase() === (pais.iso2 || '').toUpperCase() ||
             prevPais === String(pais.id))
          ) {
            opt.selected = true;
            matchFound = true;
          }

          selectPais.appendChild(opt);
        });

        if (!paisInitiallyDisabled) {
          selectPais.disabled = false;
        }

        // Si se encontró coincidencia previa o ya hay un país seleccionado
        const currentPaisVal = selectPais.value;
        if (currentPaisVal) {
          cargarDepartamentos(currentPaisVal, prevDep);
        } else {
          resetSelect(selectDep, 'Elige un país primero...', true);
          resetSelect(selectCiudad, 'Elige un departamento primero...', true);
        }
      })
      .catch(function (error) {
        console.error('Error al cargar países:', error);
        resetSelect(selectPais, 'Error al cargar países. Reintenta.', false);
      });
  }

  /**
   * Cargar Departamentos para el país seleccionado
   */
  function cargarDepartamentos(paisId, targetDepId) {
    if (!paisId) {
      resetSelect(selectDep, 'Elige un país primero...', true);
      resetSelect(selectCiudad, 'Elige un departamento primero...', true);
      return;
    }

    setLoading(selectDep, 'Cargando departamentos...');
    resetSelect(selectCiudad, 'Elige un departamento primero...', true);

    fetch(API_DEPS + encodeURIComponent(paisId) + '/')
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Error HTTP ' + response.status + ' al cargar departamentos');
        }
        return response.json();
      })
      .then(function (departamentos) {
        selectDep.innerHTML = '';

        if (!departamentos || departamentos.length === 0) {
          const emptyOpt = document.createElement('option');
          emptyOpt.value = '';
          emptyOpt.textContent = 'No hay departamentos registrados';
          selectDep.appendChild(emptyOpt);
          selectDep.disabled = true;
          return;
        }

        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'Selecciona tu departamento / estado...';
        defaultOpt.selected = true;
        defaultOpt.disabled = true;
        selectDep.appendChild(defaultOpt);

        let matchFound = false;

        departamentos.forEach(function (dep) {
          const opt = document.createElement('option');
          opt.value = dep.id;
          opt.textContent = dep.name;

          if (targetDepId && String(targetDepId) === String(dep.id)) {
            opt.selected = true;
            matchFound = true;
          }

          selectDep.appendChild(opt);
        });

        // Habilitar si el formulario no es estático de solo lectura
        if (!selectPais.hasAttribute('disabled') || !selectDep.hasAttribute('disabled')) {
          selectDep.disabled = false;
        }

        // Si se seleccionó uno previo, cargar sus ciudades
        const currentDepVal = selectDep.value;
        if (currentDepVal) {
          cargarCiudades(currentDepVal, prevCiudad);
        } else {
          resetSelect(selectCiudad, 'Elige un departamento primero...', true);
        }
      })
      .catch(function (error) {
        console.error('Error al cargar departamentos:', error);
        resetSelect(selectDep, 'Error al cargar departamentos', false);
      });
  }

  /**
   * Cargar Ciudades/Municipios para el departamento seleccionado
   */
  function cargarCiudades(depId, targetCiudadId) {
    if (!depId) {
      resetSelect(selectCiudad, 'Elige un departamento primero...', true);
      return;
    }

    setLoading(selectCiudad, 'Cargando municipios / ciudades...');

    fetch(API_CIUDADES + encodeURIComponent(depId) + '/')
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Error HTTP ' + response.status + ' al cargar ciudades');
        }
        return response.json();
      })
      .then(function (ciudades) {
        selectCiudad.innerHTML = '';

        if (!ciudades || ciudades.length === 0) {
          const emptyOpt = document.createElement('option');
          emptyOpt.value = '';
          emptyOpt.textContent = 'No hay municipios registrados';
          selectCiudad.appendChild(emptyOpt);
          selectCiudad.disabled = true;
          return;
        }

        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'Selecciona tu municipio / ciudad...';
        defaultOpt.selected = true;
        defaultOpt.disabled = true;
        selectCiudad.appendChild(defaultOpt);

        ciudades.forEach(function (ciu) {
          const opt = document.createElement('option');
          opt.value = ciu.id;
          opt.textContent = ciu.name;

          if (targetCiudadId && String(targetCiudadId) === String(ciu.id)) {
            opt.selected = true;
          }

          selectCiudad.appendChild(opt);
        });

        // Habilitar si el formulario no es estático de solo lectura
        if (!selectPais.hasAttribute('disabled') || !selectCiudad.hasAttribute('disabled')) {
          selectCiudad.disabled = false;
        }
      })
      .catch(function (error) {
        console.error('Error al cargar ciudades:', error);
        resetSelect(selectCiudad, 'Error al cargar municipios', false);
      });
  }

  // Event Listeners para interacción de usuario
  selectPais.addEventListener('change', function () {
    const selectedVal = this.value;
    cargarDepartamentos(selectedVal, null);
  });

  selectDep.addEventListener('change', function () {
    const selectedDepId = this.value;
    cargarCiudades(selectedDepId, null);
  });

  // Iniciar la carga inicial
  cargarPaises();
});
document.addEventListener('DOMContentLoaded', function () {
  const fields = [
    { id: 'id_username', name: 'username' },
    { id: 'id_email', name: 'email' },
    { id: 'id_numero_documento', name: 'numero_documento' },
    { id: 'id_telefono', name: 'telefono' }
  ];

  const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  fields.forEach(field => {
    const input = document.getElementById(field.id);
    if (!input) return;

    let debounceTimeout;

    // Debounce checking as user types
    input.addEventListener('input', function () {
      clearTimeout(debounceTimeout);
      const value = input.value.trim();

      // Al empezar a modificar/corregir, quitar temporalmente la marca is-invalid para que no quede bloqueado
      input.classList.remove('is-invalid');
      let feedback = input.parentElement.querySelector('.invalid-feedback');
      if (feedback) {
        feedback.style.display = 'none';
      }

      if (value === '') {
        resetField(input);
        return;
      }

      // Si es el campo de correo, solo consultar backend si el formato general es válido
      if (field.name === 'email') {
        if (!EMAIL_REGEX.test(value)) {
          return;
        }
      }

      debounceTimeout = setTimeout(() => {
        verificarCampo(input, field.name, value);
      }, 500);
    });

    // Verificación inmediata al salir del campo
    input.addEventListener('blur', function () {
      clearTimeout(debounceTimeout);
      const value = input.value.trim();
      if (value === '') {
        resetField(input);
        return;
      }

      if (field.name === 'email') {
        if (!EMAIL_REGEX.test(value)) {
          showError(input, 'Ingresa un correo electrónico válido (ejemplo: usuario@correo.com).');
          return;
        }
      }

      verificarCampo(input, field.name, value);
    });
  });

  function verificarCampo(input, name, value) {
    const url = `/autenticacion/verificar-campo/?campo=${name}&valor=${encodeURIComponent(value)}`;

    fetch(url)
      .then(response => {
        if (!response.ok) throw new Error('Error en la verificación');
        return response.json();
      })
      .then(data => {
        if (data.disponible === false) {
          showError(input, data.mensaje);
        } else {
          showSuccess(input);
        }
      })
      .catch(err => {
        console.error('Error al validar campo en tiempo real:', err);
      });
  }

  function showError(input, mensaje) {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');

    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (!feedback) {
      feedback = document.createElement('div');
      feedback.className = 'invalid-feedback ms-2';
      input.parentElement.appendChild(feedback);
    }
    feedback.textContent = mensaje;
    feedback.style.display = 'block';
  }

  function showSuccess(input) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');

    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
      feedback.style.display = 'none';
    }
  }

  function resetField(input) {
    input.classList.remove('is-invalid', 'is-valid');
    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
      feedback.style.display = 'none';
    }
  }

  const form = document.getElementById('formularioRegistro');
  if (form) {
    form.addEventListener('submit', function (e) {
      // Validar correo antes de enviar al servidor
      const emailInput = document.getElementById('id_email');
      if (emailInput) {
        const emailVal = emailInput.value.trim();
        if (!emailVal || !EMAIL_REGEX.test(emailVal)) {
          e.preventDefault();
          e.stopPropagation();
          showError(emailInput, 'Ingresa un correo electrónico válido (ejemplo: usuario@correo.com).');
          emailInput.focus();
          return false;
        }
      }

      // Re-verificar solo los inputs que sigan teniendo de forma explícita la clase is-invalid activa y visible
      const invalidFields = Array.from(form.querySelectorAll('.is-invalid')).filter(el => {
        const fb = el.parentElement.querySelector('.invalid-feedback');
        return fb && fb.style.display !== 'none';
      });

      if (invalidFields.length > 0) {
        e.preventDefault();
        e.stopPropagation();
        invalidFields[0].focus();
        return false;
      }
    });
  }
});
document.addEventListener('DOMContentLoaded', function () {
  const passInput = document.getElementById('pass1');
  const strengthContainer = document.getElementById('strength-container');
  const strengthBar = document.getElementById('strength-bar');
  const strengthText = document.getElementById('strength-text');
  const infoTrigger = document.getElementById('info-password-trigger');
  const requirementsCard = document.getElementById('password-requirements');

  if (!passInput) return;

  // Requirements elements
  const reqs = {
    length: { el: document.getElementById('req-length'), regex: /.{8,}/ },
    upper: { el: document.getElementById('req-upper'), regex: /[A-Z]/ },
    lower: { el: document.getElementById('req-lower'), regex: /[a-z]/ },
    number: { el: document.getElementById('req-number'), regex: /[0-9]/ },
    special: { el: document.getElementById('req-special'), regex: /[@$!%*?&._\-#]/ }
  };

  // Toggle requirements panel when info button clicked
  if (infoTrigger && requirementsCard) {
    infoTrigger.addEventListener('click', function () {
      requirementsCard.classList.toggle('d-none');
      const icon = infoTrigger.querySelector('i');
      if (icon) {
        icon.classList.toggle('bi-info-circle-fill');
        icon.classList.toggle('bi-info-circle');
      }
    });
  }

  // Monitor input to calculate strength and validate requirements
  passInput.addEventListener('input', function () {
    const password = passInput.value;

    if (password === '') {
      if (strengthContainer) strengthContainer.style.display = 'none';
      resetRequirements();
      return;
    }

    if (strengthContainer) strengthContainer.style.display = 'block';

    let score = 0;

    // Validate each requirement
    for (const key in reqs) {
      const req = reqs[key];
      const isValid = req.regex.test(password);
      if (isValid) {
        score++;
        updateReqUI(req.el, true);
      } else {
        updateReqUI(req.el, false);
      }
    }

    // Update Strength Bar UI
    updateStrengthUI(score);
  });

  function updateReqUI(el, isValid) {
    if (!el) return;
    const icon = el.querySelector('i');
    if (isValid) {
      el.classList.remove('text-secondary');
      el.classList.add('text-success', 'fw-semibold');
      if (icon) {
        icon.className = 'bi bi-check-circle-fill me-1 text-success';
      }
    } else {
      el.classList.remove('text-success', 'fw-semibold');
      el.classList.add('text-secondary');
      if (icon) {
        icon.className = 'bi bi-circle me-1 text-muted';
      }
    }
  }

  function resetRequirements() {
    for (const key in reqs) {
      updateReqUI(reqs[key].el, false);
    }
  }

  function updateStrengthUI(score) {
    if (!strengthBar || !strengthText) return;

    // Reset classes
    strengthBar.className = 'progress-bar';
    strengthText.className = 'fw-bold small';

    if (score <= 2) {
      strengthBar.style.width = '33%';
      strengthBar.classList.add('bg-danger');
      strengthText.textContent = 'Mala';
      strengthText.classList.add('text-danger');
    } else if (score <= 4) {
      strengthBar.style.width = '66%';
      strengthBar.classList.add('bg-warning');
      strengthText.textContent = 'Normal';
      strengthText.classList.add('text-warning');
    } else {
      strengthBar.style.width = '100%';
      strengthBar.classList.add('bg-success');
      strengthText.textContent = 'Buena';
      strengthText.classList.add('text-success');
    }
  }
});
