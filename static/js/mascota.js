document.addEventListener("DOMContentLoaded", function() {
    const condorImg = document.getElementById('condor-img');
    
    // Total frames available in the mascota folder (0 to 3)
    const totalFrames = 4;
    let currentFrame = 0;

    window.addEventListener('scroll', function() {
        // Calculate scroll percentage
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const maxScroll = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        
        let scrollPercent = 0;
        if (maxScroll > 0) {
            scrollPercent = scrollTop / maxScroll;
        }

        // Determine which frame to show based on scroll percentage
        let frameIndex = Math.floor(scrollPercent * totalFrames);
        
        // Prevent going out of bounds
        if (frameIndex >= totalFrames) {
            frameIndex = totalFrames - 1;
        }
        
        // Only update src if the frame has actually changed
        if (frameIndex !== currentFrame) {
            currentFrame = frameIndex;
            // Assuming static path mapping is standard, 
            // the root of your static folder translates to /static/
            condorImg.src = '/static/img/mascota/condor' + currentFrame + '.webp';
        }
    });
});
});

document.addEventListener("DOMContentLoaded", function() {
    const mascot = document.getElementById('condor-mascot-container');
    const bubble = document.getElementById('condor-speech-bubble');
    const text = document.getElementById('condor-speech-text');
    const img = document.getElementById('condor-img');
    const toggleBtn = document.getElementById('condor-toggle-btn');
    
    if (!mascot || !toggleBtn || !img) return;

    const tips = [
        "¡Hola! Soy Cóndy, tu guía en Monagua. ¡Exploremos el Páramo de Mongua juntos!",
        "¡No dejes basura en los senderos! Mantengamos el páramo limpio.",
        "¡Lleva siempre ropa abrigada e impermeable! El clima del páramo cambia rápido.",
        "¡El cóndor andino es el rey de los Andes! ¿Sabías que está en peligro de extinción?",
        "¡Sigue siempre el sendero demarcado para proteger los frailejones!",
        "¡Si tienes dudas sobre tus reservas, escríbenos a través de las PQRS!",
        "¿Sabías que la Laguna Negra es un sitio sagrado lleno de leyendas?",
        "¡El agua del páramo es vida! Respeta las fuentes hídricas naturales.",
        "Planifica tu visita con guías autorizados en nuestra pestaña de Guías y Usuarios."
    ];
    
    // Activate bouncing animation
    img.classList.add('condor-bounce');
    
    // Start collapsed on mobile devices
    if (window.innerWidth <= 768) {
        mascot.classList.add('collapsed');
    }

    // Toggle button handler
    toggleBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        mascot.classList.toggle('collapsed');
        bubble.classList.add('d-none');
        img.classList.add('condor-bounce');
    });
    
    mascot.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // If collapsed, clicking the mascot expands it instead of showing speech bubble
        if (mascot.classList.contains('collapsed')) {
            mascot.classList.remove('collapsed');
            return;
        }

        if (bubble.classList.contains('d-none')) {
            // Pick a random tip
            const randomTip = tips[Math.floor(Math.random() * tips.length)];
            text.textContent = randomTip;
            bubble.classList.remove('d-none');
            img.classList.remove('condor-bounce');
        } else {
            bubble.classList.add('d-none');
            img.classList.add('condor-bounce');
        }
    });
    
    // Close bubble when clicking anywhere else
    document.addEventListener('click', function() {
        if (bubble) bubble.classList.add('d-none');
        if (img) img.classList.add('condor-bounce');
    });
});
