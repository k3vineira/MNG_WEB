/**
 * paises_ciudades.js - Carga dinámica de países, departamentos y municipios/ciudades.
 * Actualizado para usar códigos (ISO3, DANE) como values y guardar en BD, mientras
 * se muestran los nombres completos al usuario.
 */

document.addEventListener('DOMContentLoaded', function () {
    var paisSelect = document.getElementById('id_pais');
    var deptoSelect = document.getElementById('id_departamento');
    var ciudadSelect = document.getElementById('id_ciudad');

    if (!paisSelect || !ciudadSelect) return;

    var readOnly = paisSelect.disabled;
    var countryData = [];
    var colombiaGeoData = null; // Estructura: { "15": { name: "Boyacá", munis: [ {code: "15001", name: "Tunja"} ] } }

    function toTitleCase(str) {
        if (!str) return '';
        return str.toLowerCase().replace(/(?:^|\s|-)\S/g, function (m) { return m.toUpperCase(); });
    }

    function formatLocationName(str) {
        if (!str) return '';
        var formatted = toTitleCase(str).trim();
        formatted = formatted.replace(/\bD\.c\b/g, 'D.C.');
        formatted = formatted.replace(/,\s*D\.C\./g, ' D.C.');
        formatted = formatted.replace(/\bBogota\b/g, 'Bogotá');
        return formatted;
    }

    function fetchJSON(url, options) {
        return fetch(url, options).then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        });
    }

    function getCountryNameByCode(code) {
        var c = countryData.find(function (x) { return x.iso3 === code || x.country === code; });
        return c ? c.country : code;
    }

    // 1. Cargar Países
    fetchJSON('https://countriesnow.space/api/v0.1/countries')
        .then(function (data) {
            countryData = data.data; // trae country, iso2, iso3
            paisSelect.innerHTML = '<option value="" selected disabled>Selecciona un país</option>';
            countryData.sort(function (a, b) { return a.country.localeCompare(b.country); });

            countryData.forEach(function (item) {
                var option = document.createElement('option');
                option.value = item.iso3 || item.country; // Fallback al nombre si no hay iso3
                option.textContent = item.country;
                if (paisSelect.getAttribute('data-prev') === option.value) {
                    option.selected = true;
                }
                paisSelect.appendChild(option);
            });

            if (paisSelect.value) {
                cargarDepartamentos(paisSelect.value);
            } else if (!readOnly) {
                if (deptoSelect) deptoSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
                ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
            }
        })
        .catch(function (error) { console.error('Error cargando países:', error); });

    // 2. Cargar Departamentos
    function cargarDepartamentos(selectedCountryCode) {
        if (!deptoSelect) return;
        deptoSelect.innerHTML = '<option value="" selected disabled>Cargando departamentos...</option>';
        if (!readOnly) deptoSelect.disabled = false;

        if (selectedCountryCode === 'COL' || selectedCountryCode === 'Colombia') {
            if (colombiaGeoData) {
                procesarDepartamentosColombia();
            } else {
                fetchJSON('https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=1500')
                    .then(function (data) {
                        colombiaGeoData = {};
                        data.forEach(function (item) {
                            var deptName = formatLocationName(item.dpto);
                            var deptCode = item.cod_dpto;
                            var muniName = formatLocationName(item.nom_mpio);
                            var muniCode = item.cod_mpio;
                            
                            if (deptName && muniName) {
                                if (!colombiaGeoData[deptCode]) {
                                    colombiaGeoData[deptCode] = { name: deptName, municipalities: [] };
                                }
                                var exists = colombiaGeoData[deptCode].municipalities.find(function(m) { return m.code === muniCode; });
                                if (!exists) {
                                    colombiaGeoData[deptCode].municipalities.push({ name: muniName, code: muniCode });
                                }
                            }
                        });
                        procesarDepartamentosColombia();
                    })
                    .catch(function (error) { console.error('Error cargando Colombia:', error); });
            }
        } else {
            // Para países diferentes a Colombia, establecer departamento y ciudad como 'No aplica' (vacío) y deshabilitar
            if (deptoSelect) {
                deptoSelect.innerHTML = '<option value="" selected>No aplica</option>';
                if (!readOnly) deptoSelect.disabled = true;
            }
            ciudadSelect.innerHTML = '<option value="" selected>No aplica</option>';
            if (!readOnly) ciudadSelect.disabled = true;
        }
    }

    function procesarDepartamentosColombia() {
        deptoSelect.innerHTML = '<option value="" selected disabled>Selecciona un departamento</option>';
        var depts = Object.keys(colombiaGeoData).sort(function(a, b) {
            return colombiaGeoData[a].name.localeCompare(colombiaGeoData[b].name);
        });

        depts.forEach(function (deptCode) {
            var option = document.createElement('option');
            option.value = deptCode;
            option.textContent = colombiaGeoData[deptCode].name;
            if (deptoSelect.getAttribute('data-prev') === option.value) {
                option.selected = true;
            }
            deptoSelect.appendChild(option);
        });

        if (deptoSelect.value) {
            cargarCiudades('COL', deptoSelect.value);
        } else if (!readOnly) {
            ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un departamento primero</option>';
            ciudadSelect.disabled = true;
        }
    }

    // 3. Cargar Ciudades
    function cargarCiudades(selectedCountryCode, selectedStateCode) {
        ciudadSelect.innerHTML = '<option value="" selected disabled>Cargando municipios...</option>';
        if (!readOnly) ciudadSelect.disabled = false;

        if (selectedCountryCode === 'COL' || selectedCountryCode === 'Colombia') {
            if (colombiaGeoData && colombiaGeoData[selectedStateCode]) {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona un municipio</option>';
                var municipalities = colombiaGeoData[selectedStateCode].municipalities.slice().sort(function(a, b) {
                    return a.name.localeCompare(b.name);
                });

                municipalities.forEach(function (muni) {
                    var option = document.createElement('option');
                    option.value = muni.code;
                    option.textContent = muni.name;
                    if (ciudadSelect.getAttribute('data-prev') === option.value) {
                        option.selected = true;
                    }
                    ciudadSelect.appendChild(option);
                });
            } else {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Error de departamento</option>';
            }
        } else {
            var countryName = getCountryNameByCode(selectedCountryCode);
            var stateName = selectedStateCode; 
            
            if (deptoSelect && deptoSelect.options[deptoSelect.selectedIndex]) {
                stateName = deptoSelect.options[deptoSelect.selectedIndex].textContent;
            }
            
            if (stateName === 'No aplica' || stateName === 'Selecciona un departamento') {
                return cargarCiudadesSinEstado(countryName);
            }

            fetchJSON('https://countriesnow.space/api/v0.1/countries/state/cities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country: countryName, state: stateName })
            })
            .then(function (data) {
                var cities = data.data || [];
                ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
                cities.sort(function (a, b) { return a.localeCompare(b); });
                cities.forEach(function (city) {
                    var option = document.createElement('option');
                    option.value = city; // CountriesNow no da códigos de ciudad
                    option.textContent = city;
                    if (ciudadSelect.getAttribute('data-prev') === option.value) {
                        option.selected = true;
                    }
                    ciudadSelect.appendChild(option);
                });
            })
            .catch(function (error) { console.error('Error ciudades:', error); cargarCiudadesSinEstado(countryName); });
        }
    }

    function cargarCiudadesSinEstado(countryName) {
        ciudadSelect.innerHTML = '<option value="" selected disabled>Cargando ciudades...</option>';
        if (!readOnly) ciudadSelect.disabled = false;

        var countryObj = countryData.find(function (c) { return c.country === countryName; });
        if (countryObj && countryObj.cities && countryObj.cities.length > 0) {
            ciudadSelect.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
            var cities = countryObj.cities.sort(function (a, b) { return a.localeCompare(b); });
            cities.forEach(function (city) {
                var option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                if (ciudadSelect.getAttribute('data-prev') === option.value) {
                    option.selected = true;
                }
                ciudadSelect.appendChild(option);
            });
        }
    }

    if (!readOnly) {
        paisSelect.addEventListener('change', function () {
            if (deptoSelect) {
                deptoSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
                deptoSelect.disabled = true;
            }
            ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un país primero</option>';
            ciudadSelect.disabled = true;
            cargarDepartamentos(this.value);
        });

        if (deptoSelect) {
            deptoSelect.addEventListener('change', function () {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Elige un departamento primero</option>';
                ciudadSelect.disabled = true;
                cargarCiudades(paisSelect.value, this.value);
            });
        }
    }
});
