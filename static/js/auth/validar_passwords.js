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
