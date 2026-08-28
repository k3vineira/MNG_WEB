document.addEventListener('DOMContentLoaded', function () {
  const passInput = document.getElementById('pass1');
  const strengthContainer = document.getElementById('strength-container');
  const strengthBar = document.getElementById('strength-bar');
  const strengthText = document.getElementById('strength-text');
  const infoTrigger = document.getElementById('info-password-trigger');
  const requirementsCard = document.getElementById('password-requirements');

  if (!passInput) return;

  // Requirements elements
  const reqs = {
    length: { el: document.getElementById('req-length'), regex: /.{8,}/ },
    upper: { el: document.getElementById('req-upper'), regex: /[A-Z]/ },
    lower: { el: document.getElementById('req-lower'), regex: /[a-z]/ },
    number: { el: document.getElementById('req-number'), regex: /[0-9]/ },
    special: { el: document.getElementById('req-special'), regex: /[@$!%*?&._\-#]/ }
  };

  // Toggle requirements panel when info button clicked
  if (infoTrigger && requirementsCard) {
    infoTrigger.addEventListener('click', function () {
      requirementsCard.classList.toggle('d-none');
      const icon = infoTrigger.querySelector('i');
      if (icon) {
        icon.classList.toggle('bi-info-circle-fill');
        icon.classList.toggle('bi-info-circle');
      }
    });
  }

  // Monitor input to calculate strength and validate requirements
  passInput.addEventListener('input', function () {
    const password = passInput.value;

    if (password === '') {
      if (strengthContainer) strengthContainer.style.display = 'none';
      resetRequirements();
      return;
    }

    if (strengthContainer) strengthContainer.style.display = 'block';

    let score = 0;

    // Validate each requirement
    for (const key in reqs) {
      const req = reqs[key];
      const isValid = req.regex.test(password);
      if (isValid) {
        score++;
        updateReqUI(req.el, true);
      } else {
        updateReqUI(req.el, false);
      }
    }

    // Update Strength Bar UI
    updateStrengthUI(score);
  });

  function updateReqUI(el, isValid) {
    if (!el) return;
    const icon = el.querySelector('i');
    if (isValid) {
      el.classList.remove('text-secondary');
      el.classList.add('text-success', 'fw-semibold');
      if (icon) {
        icon.className = 'bi bi-check-circle-fill me-1 text-success';
      }
    } else {
      el.classList.remove('text-success', 'fw-semibold');
      el.classList.add('text-secondary');
      if (icon) {
        icon.className = 'bi bi-circle me-1 text-muted';
      }
    }
  }

  function resetRequirements() {
    for (const key in reqs) {
      updateReqUI(reqs[key].el, false);
    }
  }

  function updateStrengthUI(score) {
    if (!strengthBar || !strengthText) return;

    // Reset classes
    strengthBar.className = 'progress-bar';
    strengthText.className = 'fw-bold small';

    if (score <= 2) {
      strengthBar.style.width = '33%';
      strengthBar.classList.add('bg-danger');
      strengthText.textContent = 'Mala';
      strengthText.classList.add('text-danger');
    } else if (score <= 4) {
      strengthBar.style.width = '66%';
      strengthBar.classList.add('bg-warning');
      strengthText.textContent = 'Normal';
      strengthText.classList.add('text-warning');
    } else {
      strengthBar.style.width = '100%';
      strengthBar.classList.add('bg-success');
      strengthText.textContent = 'Buena';
      strengthText.classList.add('text-success');
    }
  }
});
