document.addEventListener('DOMContentLoaded', function() {
    const notifBtn = document.getElementById('dropdownPanelNotif');
    const notifContainer = document.getElementById('contenedorCampanaNotif');
    if (!notifBtn || !notifContainer) return;
    
    // Logic for hiding the notification badge using localStorage
    const currentNotifCount = parseInt(notifBtn.getAttribute('data-notif-count'), 10) || 0;
    const lastSeenCount = parseInt(localStorage.getItem('notificaciones_vistas'), 10) || 0;
    const badgeCampana = document.getElementById('badgeCampanaNotif');
    const badgeDropdown = document.getElementById('badgeDropdownNotif');
    
    function hideBadges() {
        if (badgeCampana) {
            badgeCampana.classList.remove('d-flex');
            badgeCampana.classList.add('d-none');
        }
        if (badgeDropdown) {
            badgeDropdown.classList.add('d-none');
        }
    }

    // Hide badge on load if we have already seen these notifications
    if (currentNotifCount > 0 && currentNotifCount <= lastSeenCount) {
        hideBadges();
    }
    
    notifBtn.style.cursor = 'grab';
    
    let isDragging = false;
    let hasMoved = false;
    let startX = 0, startY = 0;
    let shiftX = 0, shiftY = 0;

    function startDrag(clientX, clientY) {
        isDragging = true;
        hasMoved = false;
        startX = clientX;
        startY = clientY;
        
        notifBtn.style.cursor = 'grabbing';
        let rect = notifContainer.getBoundingClientRect();
        shiftX = clientX - rect.left;
        shiftY = clientY - rect.top;
    }

    function moveAt(clientX, clientY) {
        notifContainer.style.left = (clientX - shiftX) + 'px';
        notifContainer.style.top = (clientY - shiftY) + 'px';
        notifContainer.style.right = 'auto';
        notifContainer.style.bottom = 'auto';
    }

    function onMove(e) {
        if (!isDragging) return;
        let clientX = e.touches ? e.touches[0].clientX : e.clientX;
        let clientY = e.touches ? e.touches[0].clientY : e.clientY;
        
        if (!hasMoved) {
            let dx = Math.abs(clientX - startX);
            let dy = Math.abs(clientY - startY);
            if (dx > 5 || dy > 5) hasMoved = true;
        }

        if (hasMoved) {
            if (e.touches && e.cancelable) e.preventDefault();
            moveAt(clientX, clientY);
        }
    }

    function endDrag() {
        if (!isDragging) return;
        isDragging = false;
        notifBtn.style.cursor = 'grab';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', endDrag);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', endDrag);
    }

    notifBtn.addEventListener('mousedown', function(e) {
        if (e.button !== 0) return;
        startDrag(e.clientX, e.clientY);
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', endDrag);
    });

    notifBtn.addEventListener('touchstart', function(e) {
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
        document.addEventListener('touchmove', onMove, { passive: false });
        document.addEventListener('touchend', endDrag);
    }, { passive: true });

    notifBtn.ondragstart = function() { return false; };

    notifBtn.addEventListener('click', function(e) {
        if (hasMoved) {
            e.preventDefault();
            e.stopPropagation();
            hasMoved = false;
            let bsDropdown = bootstrap.Dropdown.getInstance(notifBtn);
            if (bsDropdown) bsDropdown.hide();
        }
    }, true);

    // Only hide badges and mark as seen when a 'Detalles' button is clicked
    document.querySelectorAll('.btn-marcar-visto').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (currentNotifCount > 0) {
                localStorage.setItem('notificaciones_vistas', currentNotifCount);
                hideBadges();
            }
        });
    });
});
