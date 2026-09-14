function copiarAlPortapapeles() {
    navigator.clipboard.writeText(window.location.href);
    const txt = document.getElementById('txtCopiar');
    const btn = document.getElementById('btnCopiar');
    
    txt.innerText = '¡Copiado con éxito! ✔️';
    btn.style.backgroundColor = 'var(--verde-claro)';
    btn.style.color = '#fff';

    setTimeout(() => {
        txt.innerText = '📋 Copiar enlace del artículo';
        btn.style.backgroundColor = 'transparent';
        btn.style.color = 'var(--verde-main)';
    }, 2500);
}
