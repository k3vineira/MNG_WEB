/* otp.js - Lógica exclusiva para la verificación OTP, Restringe el input a solo números y muestra un spinner al enviar.*/

document.addEventListener('DOMContentLoaded', function () {
    var otpInput = document.getElementById('otp_input');
    var btnVerificar = document.getElementById('btn_verificar');

    // Restricción: solo números en el campo OTP
    if (otpInput) {
        otpInput.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }

    // Spinner de carga al enviar el formulario OTP
    if (otpInput && btnVerificar) {
        var form = otpInput.closest('form');
        if (form) {
            form.addEventListener('submit', function () {
                btnVerificar.disabled = true;
                btnVerificar.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Verificando...';
            });
        }
    }
});
