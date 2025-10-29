// Theme Management System for ResQNet
// Handles dark/light theme switching with localStorage persistence

document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.querySelector('.theme-toggle i');
    
    // Get saved theme from localStorage or default to 'light'
    const savedTheme = localStorage.getItem('resqnet-theme') || 'light';
    
    // Apply saved theme immediately
    applyTheme(savedTheme);
    
    // Update toggle button state
    if (savedTheme === 'dark') {
        themeIcon.className = 'fas fa-sun';
    } else {
        themeIcon.className = 'fas fa-moon';
    }
    
    // Handle theme toggle click
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        applyTheme(newTheme);
        saveTheme(newTheme);
        updateToggleIcon(newTheme);
    });
});

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        if (theme === 'dark') {
            metaThemeColor.content = '#121212';
        } else {
            metaThemeColor.content = '#6c5ce7';
        }
    }
}

function saveTheme(theme) {
    localStorage.setItem('resqnet-theme', theme);
}

function updateToggleIcon(theme) {
    const themeIcon = document.querySelector('.theme-toggle i');
    if (theme === 'dark') {
        themeIcon.className = 'fas fa-sun';
    } else {
        themeIcon.className = 'fas fa-moon';
    }
}

// Export functions for potential external use
window.ResQNetTheme = {
    applyTheme,
    saveTheme,
    updateToggleIcon,
    getCurrentTheme: () => document.documentElement.getAttribute('data-theme'),
    toggleTheme: () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        saveTheme(newTheme);
        updateToggleIcon(newTheme);
        return newTheme;
    }
};

