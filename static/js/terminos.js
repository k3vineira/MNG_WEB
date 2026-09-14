// Smooth scrolling and active state for sidebar
document.addEventListener('DOMContentLoaded', function() {
  const navLinks = document.querySelectorAll('.nav-pills-custom .nav-link');
  
  // Smooth scroll
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 30,
          behavior: 'smooth'
        });
      }
    });
  });

  // Highlight on scroll
  window.addEventListener('scroll', () => {
    let current = '';
    const sections = document.querySelectorAll('.section-card');
    
    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      if (scrollY >= sectionTop - 150) {
        current = '#' + section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === current) {
        link.classList.add('active');
      }
    });
  });
});
