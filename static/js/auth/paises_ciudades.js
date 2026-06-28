/**
 * paises_ciudades.js - Carga dinámica de países y ciudades.
 * Consume APIs externas para poblar los selectores de País y Ciudad
 * en el formulario de registro. Usa el atributo data-prev para
 * restaurar la selección previa en caso de errores de formulario.
 */

document.addEventListener('DOMContentLoaded', function () {
    var paisSelect = document.getElementById('id_pais');
    var ciudadSelect = document.getElementById('id_ciudad');

    if (!paisSelect || !ciudadSelect) return;

    var countryData = [];

    fetch('https://countriesnow.space/api/v0.1/countries')
        .then(function (response) { return response.json(); })
        .then(function (data) {
            countryData = data.data;
            paisSelect.innerHTML = '<option value="" selected disabled>Selecciona un país</option>';

            countryData.sort(function (a, b) { return a.country.localeCompare(b.country); });

            countryData.forEach(function (item) {
                var option = document.createElement('option');
                option.value = item.country;
                option.textContent = item.country;

                if (paisSelect.getAttribute('data-prev') === item.country) {
                    option.selected = true;
                }
                paisSelect.appendChild(option);
            });

            if (paisSelect.value) {
                paisSelect.dispatchEvent(new Event('change'));
            }
        })
        .catch(function (error) {
            console.error('Error cargando países:', error);
            paisSelect.outerHTML = '<input type="text" name="pais" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu país" required>';
            ciudadSelect.outerHTML = '<input type="text" name="ciudad" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu ciudad" required>';
        });

    paisSelect.addEventListener('change', function () {
        var selectedCountry = this.value;
        var ciudadElement = document.getElementById('id_ciudad');

        if (ciudadElement.tagName === 'INPUT') {
            var newSelect = document.createElement('select');
            newSelect.name = 'ciudad';
            newSelect.id = 'id_ciudad';
            newSelect.className = 'form-select rounded-4 shadow-sm text-secondary';
            newSelect.required = true;
            ciudadElement.parentNode.replaceChild(newSelect, ciudadElement);
            ciudadElement = newSelect;
        }

        ciudadElement.innerHTML = '<option value="" selected disabled>Cargando ciudades...</option>';
        ciudadElement.disabled = false;

        if (selectedCountry === 'Colombia') {
            fetch('https://api-colombia.com/api/v1/City')
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    ciudadElement.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
                    var cities = [... new Set(data.map(function (c) { return c.name; }))];
                    cities.sort(function (a, b) { return a.localeCompare(b); });

                    cities.forEach(function (city) {
                        var option = document.createElement('option');
                        option.value = city;
                        option.textContent = city;
                        if (ciudadElement.getAttribute('data-prev') === city) {
                            option.selected = true;
                        }
                        ciudadElement.appendChild(option);
                    });
                })
                .catch(function (error) {
                    console.error('Error cargando ciudades de Colombia:', error);
                    ciudadElement.outerHTML = '<input type="text" name="ciudad" id="id_ciudad" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu ciudad" required>';
                });
        } else {
            var countryObj = countryData.find(function (c) { return c.country === selectedCountry; });
            if (countryObj && countryObj.cities.length > 0) {
                ciudadElement.innerHTML = '<option value="" selected disabled>Selecciona una ciudad</option>';
                var cities = countryObj.cities.sort(function (a, b) { return a.localeCompare(b); });
                cities.forEach(function (city) {
                    var option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    if (ciudadElement.getAttribute('data-prev') === city) {
                        option.selected = true;
                    }
                    ciudadElement.appendChild(option);
                });
            } else {
                ciudadElement.outerHTML = '<input type="text" name="ciudad" id="id_ciudad" class="form-control rounded-4 shadow-sm" placeholder="Escribe tu ciudad" required>';
            }
        }
    });
});
