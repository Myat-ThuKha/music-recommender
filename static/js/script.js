document.addEventListener('DOMContentLoaded', () => {
    // Initialize particles.js

    if (document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            particles: {
                number: { value: 200,density: { enable: true, value_area: 800 } },
                color: { value: '#daa7e8' },
                shape: { type: 'image',
                    image:{
                        width: 1024,
                        height: 1024,
                        src: "/static/music_notes.png"
                    }
                },
                opacity: { value: 0.5, random: true },
                size: { value: 3, random: true },
                line_linked: { enable: true, distance: 150, color: '#daa7e8', opacity: 0.4, width: 1 },
                move: { enable: true, speed: 2, direction: 'none', random: false, straight: false, out_mode: 'out', bounce: false }
            },
            interactivity: {
                detect_on: 'canvas',
                events: { onhover: { enable: true, mode: 'repulse' }, onclick: { enable: true, mode: 'push' }, resize: true },
                modes: { repulse: { distance: 100, duration: 0.4 }, push: { particles_nb: 4 } }
            },
            retina_detect: true
        });
    }
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const username = form.querySelector('input[name="username"]');
            const password = form.querySelector('input[name="password"]');
            const rating = form.querySelector('input[name="rating"]');
            
            if (username && username.value.length < 3) {
                e.preventDefault();
                alert('Username must be at least 3 characters.');
                return;
            }
            if (password && password.value.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters.');
                return;
            }
            if (rating && (rating.value < 1 || rating.value > 5)) {
                e.preventDefault();
                alert('Rating must be between 1 and 5.');
                return;
            }
        });
    });
});