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

