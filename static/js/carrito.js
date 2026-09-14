document.addEventListener('DOMContentLoaded', function() {
  const selectAll = document.getElementById('selectAll');
  const checkboxes = Array.from(document.querySelectorAll('input[name="reservas"]'));
  const selectedCount = document.getElementById('selectedCount');
  const generateBtn = document.getElementById('generateBtn');
  const toastEl = document.getElementById('cartToast');
  const toast = toastEl ? new bootstrap.Toast(toastEl) : null;

  function updateState() {
    const selected = checkboxes.filter(cb => cb.checked).length;
    if (selectedCount) selectedCount.textContent = selected;
    if (generateBtn) generateBtn.disabled = selected === 0;
    
    // update selectAll checkbox state
    if (selectAll) {
      if (selected === checkboxes.length && checkboxes.length > 0) {
        selectAll.checked = true;
        selectAll.indeterminate = false;
      } else if (selected === 0) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
      } else {
        selectAll.checked = false;
        selectAll.indeterminate = true;
      }
    }
  }

  // bind change events
  checkboxes.forEach(cb => cb.addEventListener('change', updateState));

  if (selectAll) {
    selectAll.addEventListener('change', function() {
      const checked = this.checked;
      checkboxes.forEach(cb => cb.checked = checked);
      updateState();
    });
  }

  // form validation on submit
  const form = document.getElementById('carritoForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const anySelected = checkboxes.some(cb => cb.checked);
      if (!anySelected) {
        e.preventDefault();
        if (toast) toast.show();
      }
    });
  }

  updateState();
});
