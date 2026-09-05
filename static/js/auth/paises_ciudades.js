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
