document.addEventListener('DOMContentLoaded', function () {
  const fields = [
    { id: 'id_username', name: 'username' },
    { id: 'id_email', name: 'email' },
    { id: 'id_numero_documento', name: 'numero_documento' },
    { id: 'id_telefono', name: 'telefono' }
  ];

  fields.forEach(field => {
    const input = document.getElementById(field.id);
    if (!input) return;

    let debounceTimeout;

    // Debounce checking as user types
    input.addEventListener('input', function () {
      clearTimeout(debounceTimeout);
      const value = input.value.trim();

      if (value === '') {
        resetField(input);
        return;
      }

      debounceTimeout = setTimeout(() => {
        verificarCampo(input, field.name, value);
      }, 500);
    });

    // Immediate checking when field loses focus
    input.addEventListener('blur', function () {
      clearTimeout(debounceTimeout);
      const value = input.value.trim();
      if (value !== '') {
        verificarCampo(input, field.name, value);
      } else {
        resetField(input);
      }
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
      const invalidFields = form.querySelectorAll('.is-invalid');
      if (invalidFields.length > 0) {
        e.preventDefault();
        alert('Por favor corrige los campos con errores antes de continuar.');
      }
    });
  }
});
