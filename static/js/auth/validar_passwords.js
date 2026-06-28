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
                    btn.disabled = true;
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
