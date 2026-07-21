/* ══════════════ EFECTO DESPLIEGUE PREMIUM SINCRONIZADO ══════════════ */

// --- TRANSICIÓN DE DESPLIEGUE CONTINUO HACIA ARRIBA ---
gsap.registerPlugin(ScrollTrigger);

const wrapper = document.querySelector(".scroller-wrapper");
const panels = gsap.utils.toArray(".panel");

// PREPARACIÓN DE LAS CAPAS (ESTADOS INICIALES)
panels.forEach((panel, index) => {
    const bg = panel.querySelector('.panel-bg');
    const content = panel.querySelector('.content-box');
    
    if (index > 0) {
        // El panel de abajo inicia un 40% más abajo esperando su turno
        gsap.set(panel, { yPercent: 40 });
        
        // La imagen de abajo inicia más abajo y con baja opacidad
        gsap.set(bg, { yPercent: 15, opacity: 0.2 });
        
        // El texto de abajo inicia también abajo e invisible
        gsap.set(content, { opacity: 0, y: 100 });
    } else {
        // El primer panel inicia perfectamente centrado
        gsap.set(bg, { yPercent: 0, opacity: 1 });
        gsap.set(content, { y: 0, opacity: 1 });
    }
});

// TIMELINE MAESTRO
const tl = gsap.timeline({
    scrollTrigger: {
        trigger: wrapper,
        start: "top top",
        end: () => "+=" + (panels.length - 1) * 200 + "%", // Pista de scroll larga y fluida
        pin: true,
        scrub: 1.5, // Suavizado de inercia/retraso controlado de las cartas
        anticipatePin: 1
    }
});

// ANIMACIÓN SÍNCRONA DE DIAPOSITIVAS Y ELEMENTOS (DIRECCIÓN ÚNICA HACIA ARRIBA)
panels.forEach((panel, index) => {
    if (index < panels.length - 1) {
        const nextPanel = panels[index + 1];
        const currentBg = panel.querySelector('.panel-bg');
        const nextBg = nextPanel.querySelector('.panel-bg');
        const currentContent = panel.querySelector('.content-box');
        const nextContent = nextPanel.querySelector('.content-box');

        // 1. La diapositiva actual sube por completo hacia arriba para salir de la pantalla
        tl.to(panel, {
            yPercent: -100,
            ease: "none"
        })
        // 2. La nueva diapositiva sube sincronizadamente desde abajo
        .to(nextPanel, {
            yPercent: 0,
            ease: "none"
        }, "<")
        
        // 3. SINCRONÍA EN IMÁGENES:
        // La imagen actual sube y se desvanece
        .to(currentBg, { 
            yPercent: -15, 
            opacity: 0.2, 
            ease: "none" 
        }, "<")
        // La nueva imagen sube y se enciende
        .to(nextBg, { 
            yPercent: 0, 
            opacity: 1, 
            ease: "none" 
        }, "<")
        
        // 4. SINCRONÍA EN TEXTOS:
        // El texto actual sube y desaparece
        .to(currentContent, {
            y: -100,
            opacity: 0,
            ease: "none"
        }, "<")
        // El nuevo texto sube y aparece
        .to(nextContent, {
            opacity: 1,
            y: 0,
            ease: "power2.out"
        }, "<+=0.25"); 
    }
});

