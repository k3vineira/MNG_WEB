/**
 * toggle_password.js - Visualizador de contraseñas.
 * Alterna la visibilidad de campos de contraseña al hacer clic
 * en elementos con la clase .toggle-password y atributo data-target.
 */

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toggle-password').forEach(function (icon) {
        icon.addEventListener('click', function () {
            var targetId = this.getAttribute('data-target');
            var input = document.getElementById(targetId);
            var iconElement = this.querySelector('i');

            if (input && iconElement) {
                if (input.type === 'password') {
                    input.type = 'text';
                    iconElement.classList.remove('bi-eye');
                    iconElement.classList.add('bi-eye-slash');
                } else {
                    input.type = 'password';
                    iconElement.classList.remove('bi-eye-slash');
                    iconElement.classList.add('bi-eye');
                }
            }
        });
    });
});
