document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const increaseFontBtn = document.getElementById('increase-font');
    const decreaseFontBtn = document.getElementById('decrease-font');
    const toggleContrastBtn = document.getElementById('toggle-contrast');
    const resetFontBtn = document.getElementById('reset-font');

    let fontSize = parseInt(localStorage.getItem('fontSize')) || 100;
    let highContrast = localStorage.getItem('highContrast') === 'true';

    // Apply saved settings
    applyFontSize();
    if (highContrast) body.classList.add('high-contrast');

    if (increaseFontBtn) {
        increaseFontBtn.addEventListener('click', () => {
            if (fontSize < 150) {
                fontSize += 10;
                applyFontSize();
            }
        });
    }

    if (decreaseFontBtn) {
        decreaseFontBtn.addEventListener('click', () => {
            if (fontSize > 70) {
                fontSize -= 10;
                applyFontSize();
            }
        });
    }

    if (resetFontBtn) {
        resetFontBtn.addEventListener('click', () => {
            fontSize = 100;
            applyFontSize();
        });
    }

    if (toggleContrastBtn) {
        toggleContrastBtn.addEventListener('click', () => {
            highContrast = !highContrast;
            body.classList.toggle('high-contrast');
            localStorage.setItem('highContrast', highContrast);
        });
    }

    function applyFontSize() {
        document.documentElement.style.fontSize = fontSize + '%';
        localStorage.setItem('fontSize', fontSize);
    }
});
