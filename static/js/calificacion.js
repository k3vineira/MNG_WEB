document.addEventListener('DOMContentLoaded', function() {
  /* ── Datos ── */
  let totalCalificaciones = 0;
  let distribucionData = {};
  const dataScript = document.getElementById('calificacion-data');
  if (dataScript) {
    try {
      const data = JSON.parse(dataScript.textContent);
      totalCalificaciones = data.total || 0;
      distribucionData = data.distribucion || {};
    } catch (e) {
      console.error('Error parsing calificacion data', e);
    }
  }

  /* ── Distribución barras ── */
  if (totalCalificaciones > 0) {
    for (let i = 1; i <= 5; i++) {
      const cnt = distribucionData[i] || 0;
      const pct = Math.round((cnt / totalCalificaciones) * 100);
      const bar = document.getElementById('bar-' + i);
      const label = document.getElementById('cnt-' + i);
      if (bar) bar.style.width = pct + '%';
      if (label) label.textContent = cnt;
    }
  }

  /* ── Estrellas ── */
  const container = document.getElementById('starGeneral');
  if (container) {
    const stars = container.querySelectorAll('.star-btn');
    const input = document.getElementById('id_puntaje_estrellas');
    const paint = (upTo) => stars.forEach((s, i) => { s.classList.toggle('bi-star-fill', i < upTo); s.classList.toggle('bi-star', i >= upTo); });
    paint(parseInt(input.value) || 5);
    stars.forEach((star, idx) => {
      star.addEventListener('click', () => { input.value = idx + 1; paint(idx + 1); });
      star.addEventListener('mouseover', () => paint(idx + 1));
      star.addEventListener('mouseout', () => paint(parseInt(input.value) || 5));
    });
  }

  /* ── Contador de caracteres ── */
  const textarea = document.getElementById('id_comentario');
  const charCount = document.getElementById('char-count');
  if (textarea && charCount) {
    textarea.addEventListener('input', () => {
      const len = textarea.value.length;
      charCount.textContent = len + ' / 500';
      charCount.classList.toggle('text-danger', len >= 480);
      charCount.classList.toggle('text-muted', len < 480);
    });
  }

  /* ── Paginación de calificaciones (5 por página) ── */
  const PER_PAGE = 5;
  const items = Array.from(document.querySelectorAll('.calificacion-item'));
  const controls = document.getElementById('pagination-controls');
  
  if (items.length && controls) {
    let currentPage = 1;
    const totalPages = Math.ceil(items.length / PER_PAGE);

    function showPage(page) {
      currentPage = page;
      items.forEach((el, idx) => {
        const start = (page - 1) * PER_PAGE;
        el.style.display = (idx >= start && idx < start + PER_PAGE) ? 'block' : 'none';
      });
      renderControls();
    }

    function renderControls() {
      controls.innerHTML = '';
      if (totalPages <= 1) return;

      // Botón anterior
      const prev = document.createElement('button');
      prev.className = 'btn btn-sm btn-outline-secondary rounded-3';
      prev.innerHTML = '<i class="bi bi-chevron-left"></i>';
      prev.disabled = currentPage === 1;
      prev.addEventListener('click', () => {
        showPage(currentPage - 1);
        document.getElementById('calificaciones-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      controls.appendChild(prev);

      // Páginas numeradas
      for (let p = 1; p <= totalPages; p++) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm rounded-3 ' + (p === currentPage ? 'btn-success' : 'btn-outline-secondary');
        btn.textContent = p;
        btn.addEventListener('click', () => {
          showPage(p);
          document.getElementById('calificaciones-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        controls.appendChild(btn);
      }

      // Botón siguiente
      const next = document.createElement('button');
      next.className = 'btn btn-sm btn-outline-secondary rounded-3';
      next.innerHTML = '<i class="bi bi-chevron-right"></i>';
      next.disabled = currentPage === totalPages;
      next.addEventListener('click', () => {
        showPage(currentPage + 1);
        document.getElementById('calificaciones-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      controls.appendChild(next);
    }

    showPage(1);
  }
});
