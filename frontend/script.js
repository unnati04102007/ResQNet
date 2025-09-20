// Page Navigation
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
  closeMenu();
}

// Language Toggle
let currentLang = 'en';
function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'hi' : 'en';
  document.getElementById("langBtn").innerText = currentLang === 'en' ? "🌍 EN" : "🌍 HI";
  document.querySelectorAll('[data-en]').forEach(el => {
    el.textContent = el.getAttribute(`data-${currentLang}`);
  });
}

// Dark Mode Toggle
function toggleTheme() {
  document.body.classList.toggle("dark");
  document.getElementById("themeBtn").innerText = 
    document.body.classList.contains("dark") ? "☀️" : "🌙";
}

// Mobile Menu Toggle
function toggleMenu() {
  document.getElementById("navMenu").classList.toggle("show");
}
function closeMenu() {
  document.getElementById("navMenu").classList.remove("show");
}
