/**
 * paises_ciudades.js - Carga dinámica de países, departamentos y municipios/ciudades.
 * Consume APIs externas para poblar los selectores en cascada en el formulario de registro y perfil.
 * Usa el atributo data-prev para restaurar la selección previa en caso de recargas de formulario.
 *
 * Si los selects están inicialmente deshabilitados (ej: perfil),
 * opera en modo solo lectura: carga y preselecciona, pero NO los habilita.
 */

document.addEventListener('DOMContentLoaded', function () {
    var paisSelect = document.getElementById('id_pais');
    var deptoSelect = document.getElementById('id_departamento');
    var ciudadSelect = document.getElementById('id_ciudad');

    if (!paisSelect || !ciudadSelect) return;

    // Detectar modo solo lectura: si el select de país viene disabled en el HTML
    var readOnly = paisSelect.disabled;
    var countryData = [];
    var colombiaGeoData = null; // Caché para los datos de Colombia (departamentos y municipios)

    // Helper para formatear nombres a Title Case con excepciones como D.C. y acentos
    function toTitleCase(str) {
        if (!str) return '';
        return str.toLowerCase().replace(/(?:^|\s|-)\S/g, function (m) {
            return m.toUpperCase();
        });
    }

    function formatLocationName(str) {
        if (!str) return '';
        var formatted = toTitleCase(str).trim();
        formatted = formatted.replace(/\bD\.c\b/g, 'D.C.');
        formatted = formatted.replace(/,\s*D\.C\./g, ' D.C.');
        formatted = formatted.replace(/\bBogota\b/g, 'Bogotá');
        return formatted;
    }

    // Helper para comparar nombres geográficos ignorando acentos, puntuación y mayúsculas
    function namesMatch(a, b) {
        if (!a || !b) return false;
        var clean = function (s) {
            return s.toLowerCase()
                .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                .replace(/[^a-z0-9]/g, "");
        };
        return clean(a) === clean(b);
    }

    // Función de fallback si las llamadas API fallan por completo
    function activarEntradasFallback() {
        if (readOnly) {
            var prevPais = paisSelect.getAttribute('data-prev') || 'No especificado';
            var prevDepto = deptoSelect ? (deptoSelect.getAttribute('data-prev') || 'No especificado') : 'No especificado';
            var prevCiudad = ciudadSelect.getAttribute('data-prev') || 'No especificado';

            paisSelect.outerHTML = '<input type="text" id="id_pais" class="form-control rounded-4 shadow-sm bg-light text-muted" value="' + prevPais + '" disabled readonly>';
            if (deptoSelect) {
                deptoSelect.outerHTML = '<input type="text" id="id_departamento" class="form-control rounded-4 shadow-sm bg-light text-muted" value="' + prevDepto + '" disabled readonly>';
            }
            ciudadSelect.outerHTML = '<input type="text" id="id_ciudad" class="form-control rounded-4 shadow-sm bg-light text-muted" value="' + prevCiudad + '" disabled readonly>';
        } else {
            paisSelect.outerHTML = '<input type="text" name="pais" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu país" required>';
            if (deptoSelect) {
                deptoSelect.outerHTML = '<input type="text" name="departamento" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu departamento">';
            }
            ciudadSelect.outerHTML = '<input type="text" name="ciudad" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu ciudad" required>';
        }
    }

    // Helper para realizar fetch de JSON de forma segura
    function fetchJSON(url, options) {
        return fetch(url, options).then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        });
    }

    // 1. Cargar el listado de países (de CountriesNow)
    fetchJSON('https://countriesnow.space/api/v0.1/countries')
        .then(function (data) {
            countryData = data.data;
            paisSelect.innerHTML = '<option value="" selected disabled>Selecciona un país</option>';

            countryData.sort(function (a, b) { return a.country.localeCompare(b.country); });

            countryData.forEach(function (item) {
                var option = document.createElement('option');
                option.value = item.country;
                option.textContent = item.country;
                if (namesMatch(paisSelect.getAttribute('data-prev'), item.country)) {
                    option.selected = true;
                }
                paisSelect.appendChild(option);
            });

            // Si hay un país preseleccionado, cargar sus departamentos
            if (paisSelect.value) {
                cargarDepartamentos(paisSelect.value);
            } else if (!readOnly) {
                if (deptoSelect) deptoSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
                ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
            }
        })
        .catch(function (error) {
            console.error('Error cargando países:', error);
            activarEntradasFallback();
        });

    // 2. Cargar departamentos/estados
    function cargarDepartamentos(selectedCountry) {
        if (!deptoSelect) return;

        deptoSelect.innerHTML = '<option value="" selected disabled>Cargando departamentos...</option>';
        if (!readOnly) deptoSelect.disabled = false;

        if (selectedCountry === 'Colombia') {
            // Si ya tenemos los datos en caché, los procesamos de inmediato
            if (colombiaGeoData) {
                procesarDepartamentosColombia();
            } else {
                // Consumir la API oficial de datos abiertos del gobierno de Colombia (DIVIPOLA)
                fetchJSON('https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=1500')
                    .then(function (data) {
                        colombiaGeoData = {};
                        data.forEach(function (item) {
                            var dept = formatLocationName(item.dpto);
                            var muni = formatLocationName(item.nom_mpio);
                            if (dept && muni) {
                                if (!colombiaGeoData[dept]) {
                                    colombiaGeoData[dept] = [];
                                }
                                if (colombiaGeoData[dept].indexOf(muni) === -1) {
                                    colombiaGeoData[dept].push(muni);
                                }
                            }
                        });
                        procesarDepartamentosColombia();
                    })
                    .catch(function (error) {
                        console.error('Error cargando departamentos oficiales de Colombia:', error);
                        activarEntradasFallback();
                    });
            }
        } else {
            // Para otros países, obtener subdivisiones de CountriesNow
            fetchJSON('https://countriesnow.space/api/v0.1/countries/states', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country: selectedCountry })
            })
            .then(function (data) {
                var states = data.data && data.data.states ? data.data.states : [];
                if (states.length === 0) {
                    // Si no tiene estados en la API, cargar las ciudades directamente
                    deptoSelect.innerHTML = '<option value="" selected>No aplica</option>';
                    if (!readOnly) deptoSelect.disabled = true;
                    cargarCiudadesSinEstado(selectedCountry);
                } else {
                    deptoSelect.innerHTML = '<option value="" selected disabled>Selecciona un departamento</option>';
                    states.sort(function (a, b) { return a.name.localeCompare(b.name); });

                    states.forEach(function (state) {
                        var option = document.createElement('option');
                        option.value = state.name;
                        option.textContent = state.name;
                        if (namesMatch(deptoSelect.getAttribute('data-prev'), state.name)) {
                            option.selected = true;
                        }
                        deptoSelect.appendChild(option);
                    });

                    // Si hay departamento seleccionado, cargar ciudades
                    if (deptoSelect.value) {
                        cargarCiudades(selectedCountry, deptoSelect.value);
                    } else if (!readOnly) {
                        ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un departamento primero</option>';
                        ciudadSelect.disabled = true;
                    }
                }
            })
            .catch(function (error) {
                console.warn('Error cargando estados, cargando ciudades directamente:', error);
                deptoSelect.innerHTML = '<option value="" selected>No aplica</option>';
                if (!readOnly) deptoSelect.disabled = true;
                cargarCiudadesSinEstado(selectedCountry);
            });
        }
    }

    // Procesa los departamentos cacheados de Colombia en el select correspondiente
    function procesarDepartamentosColombia() {
        deptoSelect.innerHTML = '<option value="" selected disabled>Selecciona un departamento</option>';
        var depts = Object.keys(colombiaGeoData).sort(function (a, b) { return a.localeCompare(b); });

        depts.forEach(function (deptName) {
            var option = document.createElement('option');
            option.value = deptName;
            option.textContent = deptName;
            if (namesMatch(deptoSelect.getAttribute('data-prev'), deptName)) {
                option.selected = true;
            }
            deptoSelect.appendChild(option);
        });

        // Si hay un departamento preseleccionado, cargar sus ciudades
        if (deptoSelect.value) {
            cargarCiudades('Colombia', deptoSelect.value);
        } else if (!readOnly) {
            ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un departamento primero</option>';
            ciudadSelect.disabled = true;
        }
    }

    // 3. Cargar ciudades/municipios con base en un departamento/estado
    function cargarCiudades(selectedCountry, selectedState) {
        ciudadSelect.innerHTML = '<option value="" selected disabled>Cargando municipios...</option>';
        if (!readOnly) ciudadSelect.disabled = false;

        if (selectedCountry === 'Colombia') {
            if (colombiaGeoData && colombiaGeoData[selectedState]) {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona un municipio</option>';
                var municipalities = colombiaGeoData[selectedState].slice().sort(function (a, b) { return a.localeCompare(b); });

                municipalities.forEach(function (muni) {
                    var option = document.createElement('option');
                    option.value = muni;
                    option.textContent = muni;
                    if (namesMatch(ciudadSelect.getAttribute('data-prev'), muni)) {
                        option.selected = true;
                    }
                    ciudadSelect.appendChild(option);
                });
            } else {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Error de departamento</option>';
            }
        } else {
            // Para otros países, obtener ciudades de ese estado de CountriesNow
            fetchJSON('https://countriesnow.space/api/v0.1/countries/state/cities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country: selectedCountry, state: selectedState })
            })
            .then(function (data) {
                var cities = data.data || [];
                ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
                cities.sort(function (a, b) { return a.localeCompare(b); });

                cities.forEach(function (city) {
                    var option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    if (namesMatch(ciudadSelect.getAttribute('data-prev'), city)) {
                        option.selected = true;
                    }
                    ciudadSelect.appendChild(option);
                });
            })
            .catch(function (error) {
                console.warn('Error cargando ciudades por estado, cargando listado directo del país:', error);
                cargarCiudadesSinEstado(selectedCountry);
            });
        }
    }

    // 4. Cargador secundario de ciudades para un país sin estados/divisiones
    function cargarCiudadesSinEstado(selectedCountry) {
        ciudadSelect.innerHTML = '<option value="" selected disabled>Cargando ciudades...</option>';
        if (!readOnly) ciudadSelect.disabled = false;

        var countryObj = countryData.find(function (c) { return c.country === selectedCountry; });
        if (countryObj && countryObj.cities && countryObj.cities.length > 0) {
            ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
            var cities = countryObj.cities.sort(function (a, b) { return a.localeCompare(b); });

            cities.forEach(function (city) {
                var option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                if (namesMatch(ciudadSelect.getAttribute('data-prev'), city)) {
                    option.selected = true;
                }
                ciudadSelect.appendChild(option);
            });
        } else {
            ciudadSelect.innerHTML = '<option value="" selected disabled>No se encontraron ciudades</option>';
            if (!readOnly) {
                ciudadSelect.outerHTML = '<input type="text" name="ciudad" id="id_ciudad" class="form-select rounded-4 shadow-sm" placeholder="Escribe tu ciudad" required>';
            }
        }
    }

    // Asociar eventos solo en modo interactivo/edición
    if (!readOnly) {
        paisSelect.addEventListener('change', function () {
            var selectedCountry = this.value;
            if (deptoSelect) {
                deptoSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
                deptoSelect.disabled = true;
            }
            ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
            ciudadSelect.disabled = true;

            if (selectedCountry) {
                cargarDepartamentos(selectedCountry);
            }
        });

        if (deptoSelect) {
            deptoSelect.addEventListener('change', function () {
                var selectedCountry = paisSelect.value;
                var selectedState = this.value;
                ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un departamento primero</option>';
                ciudadSelect.disabled = true;

                if (selectedCountry && selectedState !== undefined) {
                    if (selectedState === "") {
                        cargarCiudadesSinEstado(selectedCountry);
                    } else {
                        cargarCiudades(selectedCountry, selectedState);
                    }
                }
            });
        }
    }
});
