/* ══════════════ HERO - EFECTO RASTRO DE AGUA (METABALLS) ══════════════ */

// Detectar móviles reales (táctiles sin mouse) en lugar de laptops con pantalla táctil
const isMobileDevice = window.matchMedia("(hover: none) and (pointer: coarse)").matches;

const canvas = document.getElementById('waterCanvas');
const ctx = canvas.getContext('2d');
const interfaceEl = document.querySelector('.interface');

const mainParticles = [];
let trailParticles = [];
const bgBubbles = [];
const mouse = { x: null, y: null, vx: 0, vy: 0, lastX: 0, lastY: 0 };

let targetCenter = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
let currentScale = 0;
let targetScale = 0;
let time = 0;
let firstMove = true;
let autoPilot = true; // Auto-pilot activo por defecto en todos los dispositivos
let lastInteractionTime = 0;

// Variables para escalas dinámicas de tamaños entre piloto automático e interacción
let currentMainScaleFactor = 1.0;
let currentTrailScaleFactor = 1.0;

function resizeCanvas() {
  canvas.width = document.documentElement.clientWidth || window.innerWidth;
  canvas.height = window.innerHeight;
  initMainFluidBlob();
}

// CLASE 1: Burbuja central principal del mouse
class MainParticle {
  constructor(radiusFromCenter, angle, maxRadius) {
    this.angle = angle;
    this.radiusFromCenter = radiusFromCenter;
    this.relativeRadius = radiusFromCenter / maxRadius;

    this.ox = Math.cos(angle) * radiusFromCenter;
    this.oy = Math.sin(angle) * radiusFromCenter;

    this.x = targetCenter.x + this.ox;
    this.y = targetCenter.y + this.oy;

    this.vx = 0;
    this.vy = 0;
    this.size = this.relativeRadius < 0.4 ? Math.random() * 4 + 16 : Math.random() * 5 + 10;
  }

  update(center, scale) {
    const ripple = Math.sin(time * 2.5 + this.radiusFromCenter * 0.15 + this.angle * 3) * 3.5;
    const targetX = center.x + (this.ox + Math.cos(this.angle) * ripple) * scale;
    const targetY = center.y + (this.oy + Math.sin(this.angle) * ripple) * scale;

    const elasticity = 0.12 - (this.relativeRadius * 0.08);
    const friction = 0.76 + (this.relativeRadius * 0.06);

    this.vx += (targetX - this.x) * elasticity;
    this.vy += (targetY - this.y) * elasticity;

    this.vx *= friction;
    this.vy *= friction;

    this.x += this.vx;
    this.y += this.vy;
  }

  draw(scale) {
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(this.x, this.y, Math.max(0, this.size * scale * currentMainScaleFactor), 0, Math.PI * 2);
    ctx.fill();
  }
}

// CLASE 2: Rastro de larga duración
class TrailParticle {
  constructor(x, y, mouseVx, mouseVy) {
    this.x = x;
    this.y = y;

    this.vx = mouseVx * 0.06 + (Math.random() - 0.5) * 0.4;
    this.vy = mouseVy * 0.06 + (Math.random() - 0.5) * 0.4;

    this.initialSize = Math.random() * 4 + 14;
    this.size = this.initialSize;
    this.life = 1.0;

    this.decay = Math.random() * 0.002 + 0.004;
  }

  update() {
    const currentNoiseX = Math.sin(time * 1.5 + this.y * 0.04) * 0.15;
    const currentNoiseY = Math.cos(time * 1.5 + this.x * 0.04) * 0.15;

    this.vx += currentNoiseX;
    this.vy += currentNoiseY;

    this.vx *= 0.92;
    this.vy *= 0.92;

    this.x += this.vx;
    this.y += this.vy;

    this.life -= this.decay;
    this.size = this.initialSize * this.life;
  }

  draw() {
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(this.x, this.y, Math.max(0, this.size * currentTrailScaleFactor), 0, Math.PI * 2);
    ctx.fill();
  }
}

// CLASE 3: Burbujas flotantes de fondo
class BackgroundBubble {
  constructor() {
    this.x = Math.random() * window.innerWidth;
    this.y = Math.random() * window.innerHeight;
    this.baseSize = Math.random() * 35 + 15; 
    this.size = this.baseSize;
    this.vx = (Math.random() - 0.5) * 0.5;
    this.vy = (Math.random() - 0.5) * 0.5;
    this.phase = Math.random() * Math.PI * 2;
    this.phaseSpeed = Math.random() * 0.02 + 0.01;
  }

  update() {
    this.phase += this.phaseSpeed;
    this.x += this.vx + Math.sin(this.phase) * 0.3;
    this.y += this.vy + Math.cos(this.phase) * 0.3;
    this.size = this.baseSize + Math.sin(time * 2 + this.phase) * (this.baseSize * 0.15);

    if (this.x < -100) this.x = canvas.width + 100;
    if (this.x > canvas.width + 100) this.x = -100;
    if (this.y < -100) this.y = canvas.height + 100;
    if (this.y > canvas.height + 100) this.y = -100;
  }

  draw() {
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(this.x, this.y, Math.max(0, this.size), 0, Math.PI * 2);
    ctx.fill();
  }
}

function initMainFluidBlob() {
  mainParticles.length = 0;
  const layers = 20;
  const layerSpacing = 6.5;
  const maxRadius = layers * layerSpacing;

  for (let l = 1; l <= layers; l++) {
    const radius = l * layerSpacing;
    const density = Math.floor(radius * 0.75);

    for (let i = 0; i < density; i++) {
      const angle = (i / density) * Math.PI * 2;
      mainParticles.push(new MainParticle(radius, angle, maxRadius));
    }
  }
}

function animate() {
  time += 0.02;
  const now = Date.now();

  // Transiciones de escala suaves entre Piloto Automático (Main pequeña, Rastro grande) y Mouse (Normal)
  const targetMainScale = autoPilot ? 0.35 : 1.0;
  const targetTrailScale = autoPilot ? 1.70 : 1.0;
  currentMainScaleFactor += (targetMainScale - currentMainScaleFactor) * 0.05;
  currentTrailScaleFactor += (targetTrailScale - currentTrailScaleFactor) * 0.05;

  if (autoPilot) {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    // Frecuencias reducidas para un movimiento mucho más lento, suave y elegante
    const autoX = centerX + Math.sin(time * 0.5) * (canvas.width * 0.35);
    const autoY = centerY + Math.sin(time * 0.3) * (canvas.height * 0.22);
    
    if (firstMove) {
      targetCenter.x = autoX;
      targetCenter.y = autoY;
      mouse.lastX = autoX;
      mouse.lastY = autoY;
      firstMove = false;
    }
    mouse.x = autoX;
    mouse.y = autoY;
  } else {
    // Retornar a piloto automático tras 3 segundos de inactividad
    if (now - lastInteractionTime > 3000 && !isMobileDevice) {
      autoPilot = true;
      firstMove = true; // Para transición suave
    }
  }

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  mouse.vx = mouse.x - mouse.lastX;
  mouse.vy = mouse.y - mouse.lastY;
  const mouseSpeed = Math.sqrt(mouse.vx * mouse.vx + mouse.vy * mouse.vy);

  if (mouse.x !== null) {
    targetScale = 1;
    // Inercia líquida y suavizado del centro: más lento en piloto automático
    const followSpeed = autoPilot ? 0.04 : 0.16;
    targetCenter.x += (mouse.x - targetCenter.x) * followSpeed;
    targetCenter.y += (mouse.y - targetCenter.y) * followSpeed;

    // Generar rastro constante en piloto automático
    if (autoPilot) {
      if (Math.floor(time * 50) % 2 === 0) {
        trailParticles.push(new TrailParticle(targetCenter.x, targetCenter.y, mouse.vx * 0.3, mouse.vy * 0.3));
      }
    } else if (mouseSpeed > 1.2 && !firstMove) {
      const steps = Math.min(Math.floor(mouseSpeed / 5), 5);

      for (let i = 0; i < steps; i++) {
        const alpha = i / steps;
        const interpolatedX = mouse.lastX + (mouse.x - mouse.lastX) * alpha;
        const interpolatedY = mouse.lastY + (mouse.y - mouse.lastY) * alpha;

        trailParticles.push(new TrailParticle(interpolatedX, interpolatedY, mouse.vx, mouse.vy));
      }
    }
  } else {
    targetScale = 0;
    mouse.vx = 0;
    mouse.vy = 0;
  }

  mouse.lastX = mouse.x;
  mouse.lastY = mouse.y;

  currentScale += (targetScale - currentScale) * 0.08;

  trailParticles = trailParticles.filter(p => p.life > 0);
  for (let i = 0; i < trailParticles.length; i++) {
    trailParticles[i].update();
    trailParticles[i].draw();
  }

  for (let i = 0; i < mainParticles.length; i++) {
    mainParticles[i].update(targetCenter, currentScale);
    mainParticles[i].draw(currentScale);
  }

  // Detectar si la burbuja principal está sobre el bloque de texto
  if (interfaceEl && currentScale > 0.05) {
    const rect = interfaceEl.getBoundingClientRect();
    const blobRadius = 130 * currentScale * currentMainScaleFactor;
    const over =
      targetCenter.x + blobRadius > rect.left &&
      targetCenter.x - blobRadius < rect.right &&
      targetCenter.y + blobRadius > rect.top  &&
      targetCenter.y - blobRadius < rect.bottom;

    if (over) {
      interfaceEl.classList.add('hero-text-light');
    } else {
      interfaceEl.classList.remove('hero-text-light');
    }
  } else if (interfaceEl) {
    interfaceEl.classList.remove('hero-text-light');
  }

  requestAnimationFrame(animate);
}

window.addEventListener('mousemove', (e) => {
  if (isMobileDevice) return;
  autoPilot = false;
  lastInteractionTime = Date.now();

  const rect = canvas.getBoundingClientRect();
  const clientX = e.clientX - rect.left;
  const clientY = e.clientY - rect.top;

  if (firstMove) {
    targetCenter.x = clientX;
    targetCenter.y = clientY;
    mouse.lastX = clientX;
    mouse.lastY = clientY;
    firstMove = false;
  }
  mouse.x = clientX;
  mouse.y = clientY;
});

window.addEventListener('touchmove', (e) => {
  if (e.touches.length > 0) {
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches[0].clientX - rect.left;
    const clientY = e.touches[0].clientY - rect.top;

    if (firstMove) {
      targetCenter.x = clientX;
      targetCenter.y = clientY;
      mouse.lastX = clientX;
      mouse.lastY = clientY;
      firstMove = false;
    }
    mouse.x = clientX;
    mouse.y = clientY;
  }
});

window.addEventListener('touchend', () => {
  mouse.x = null;
  mouse.y = null;
});

window.addEventListener('touchcancel', () => {
  mouse.x = null;
  mouse.y = null;
});

window.addEventListener('mouseleave', () => {
  if (!isMobileDevice) {
    autoPilot = true;
    firstMove = true;
  }
});

window.addEventListener('resize', resizeCanvas);

resizeCanvas();
animate();
