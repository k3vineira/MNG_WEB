document.addEventListener('DOMContentLoaded', function() {
    const imgComprobante = document.getElementById('id_imagen_comprobante');
    if (imgComprobante) {
        imgComprobante.addEventListener('change', function(event) {
            let previewContainer = document.getElementById('previewContainer');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.id = 'previewContainer';
                previewContainer.className = 'mt-3 d-none';
                previewContainer.innerHTML = `
                    <p class="small text-muted mb-2">Vista previa de la imagen cargada:</p>
                    <img id="previewImagen" class="img-fluid img-thumbnail rounded-4 shadow-sm" style="max-height: 300px; object-fit: contain; width: auto;" alt="Vista previa">
                `;
                event.target.parentNode.appendChild(previewContainer);
            }
            const previewImage = document.getElementById('previewImagen');
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                }
                reader.readAsDataURL(file);
            } else {
                previewImage.src = '';
                previewContainer.classList.add('d-none');
            }
        });
    }

    const bancoOrigen = document.getElementById('id_banco_origen');
    if (bancoOrigen) {
        bancoOrigen.addEventListener('change', function() {
            const descField = document.getElementById('id_descripcion');
            if (descField) {
                if (this.value === 'Otro') {
                    descField.setAttribute('placeholder', 'Especifica tu banco o medio de pago aquí...');
                    descField.focus();
                } else {
                    descField.setAttribute('placeholder', 'Notas o Detalles Adicionales');
                }
            }
        });
    }
});
