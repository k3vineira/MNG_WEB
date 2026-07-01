/**
 * validar_passwords.js - Validación de coincidencia de contraseñas.
 * Compara los campos pass1 y pass2 antes de enviar el formulario.
 * Funciona tanto en el registro (#formularioRegistro) como en el
 * restablecimiento de contraseña (#form_reset).
 */

document.addEventListener('DOMContentLoaded', function () {
    var formRegistro = document.getElementById('formularioRegistro');
    var formReset = document.getElementById('form_reset');
    var msgError = document.getElementById('mensajeError');
    var pass1 = document.getElementById('pass1');
    var strengthBar = document.getElementById('password-strength-bar');
    var strengthText = document.getElementById('password-strength-text');

    if (pass1 && strengthBar && strengthText) {
        pass1.addEventListener('input', function () {
            var val = pass1.value;
            if (val.length === 0) {
                strengthBar.className = 'progress-bar bg-secondary';
                strengthBar.style.width = '0%';
                strengthText.textContent = 'Contraseña no ingresada';
                strengthText.className = 'text-muted d-block mt-1 small';
            } else if (val.length < 6) {
                strengthBar.className = 'progress-bar bg-danger';
                strengthBar.style.width = '33%';
                strengthText.textContent = 'No es segura';
                strengthText.className = 'text-danger d-block mt-1 small fw-bold';
            } else {
                var hasLetters = /[a-zA-Z]/.test(val);
                var hasNumbers = /[0-9]/.test(val);
                
                if (val.length >= 8 && hasLetters && hasNumbers) {
                    strengthBar.className = 'progress-bar bg-success';
                    strengthBar.style.width = '100%';
                    strengthText.textContent = 'Contraseña segura';
                    strengthText.className = 'text-success d-block mt-1 small fw-bold';
                } else {
                    strengthBar.className = 'progress-bar bg-warning';
                    strengthBar.style.width = '66%';
                    strengthText.textContent = 'Contraseña regular';
                    strengthText.className = 'text-warning d-block mt-1 small fw-bold';
                }
            }
        });
    }

    function validatePasswordMatch(event, btn) {
        var pass1 = document.getElementById('pass1');
        var pass2 = document.getElementById('pass2');

        if (pass1 && pass2) {
            if (pass1.value !== pass2.value) {
                event.preventDefault();
                if (msgError) {
                    msgError.classList.remove('d-none');
                }
            } else {
                if (msgError) {
                    msgError.classList.add('d-none');
                }
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

    function setupRealTimeCheck(inputId, feedbackId, fieldName) {
        var inputEl = document.getElementById(inputId);
        var feedbackEl = document.getElementById(feedbackId);
        if (inputEl && feedbackEl) {
            inputEl.addEventListener('input', function () {
                var value = inputEl.value.trim();
                if (value === "") {
                    inputEl.classList.remove('is-invalid');
                    inputEl.classList.remove('is-valid');
                    feedbackEl.textContent = "";
                    return;
                }
                fetch('/autenticacion/verificar-disponibilidad/?field=' + fieldName + '&value=' + encodeURIComponent(value))
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (data) {
                        if (!data.available) {
                            inputEl.classList.add('is-invalid');
                            inputEl.classList.remove('is-valid');
                            feedbackEl.textContent = data.message;
                        } else {
                            inputEl.classList.remove('is-invalid');
                            inputEl.classList.add('is-valid');
                            feedbackEl.textContent = "";
                        }
                    })
                    .catch(function (error) {
                        console.error('Error verificando disponibilidad:', error);
                    });
            });
        }
    }

    setupRealTimeCheck('id_username', 'feedback_username', 'username');
    setupRealTimeCheck('id_email', 'feedback_email', 'email');
    setupRealTimeCheck('id_numero_documento', 'feedback_numero_documento', 'numero_documento');
    setupRealTimeCheck('id_telefono', 'feedback_telefono', 'telefono');
});
