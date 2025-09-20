<<<<<<< HEAD
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
=======
// ===============================
// DOM READY
// ===============================
document.addEventListener("DOMContentLoaded", () => {

  // ===============================
  // Navigation (SPA-like behavior)
  // ===============================
  const navLinks = document.querySelectorAll(".nav-links a");
  const pages = document.querySelectorAll(".page");

  function showPage(pageId) {
    // Remove active from all
    navLinks.forEach(nav => nav.classList.remove("active"));
    pages.forEach(page => page.classList.remove("active"));

    // Add active to clicked link + section
    const targetLink = document.querySelector(`.nav-links a[href="#${pageId}"]`);
    const targetPage = document.getElementById(pageId);

    if (targetLink) targetLink.classList.add("active");
    if (targetPage) targetPage.classList.add("active");
  }

  // Navigation click handling
  navLinks.forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const targetId = link.getAttribute("href").substring(1);
      showPage(targetId);
    });
  });

  // Default: show Home page
  showPage("home");

  // ===============================
  // Dark Mode Toggle 🌙/☀
  // ===============================
  const darkToggle = document.getElementById("darkToggle");
  if (darkToggle) {
    darkToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark");
      darkToggle.textContent = document.body.classList.contains("dark") ? "☀" : "🌙";
    });
  }

  // ===============================
  // Multilingual Toggle 🌐
  // ===============================
  const langToggle = document.getElementById("langToggle");
  let currentLang = "en";

  const translations = {
    en: {
      home: "Home",
      report: "Report",
      donation: "Donation",
      register: "Register",
      login: "Login",
      contact: "Contact Us",
      feedback: "Feedback",
      alert: "🚨 Emergency Alert: Placeholder for urgent updates or warnings.",
      aboutTitle: "About ResQNet",
      aboutText: "ResQNet is a next-generation disaster management system designed to help communities prepare for, respond to, and recover from emergencies."
    },
    hi: {
      home: "होम",
      report: "रिपोर्ट",
      donation: "दान",
      register: "पंजीकरण",
      login: "लॉगिन",
      contact: "संपर्क करें",
      feedback: "फीडबैक",
      alert: "🚨 आपातकालीन चेतावनी: यहां ताज़ा अपडेट और चेतावनियां दिखाई देंगी।",
      aboutTitle: "रेस्क्यूनेट के बारे में",
      aboutText: "रेस्क्यूनेट एक अगली पीढ़ी की आपदा प्रबंधन प्रणाली है, जो समुदायों को आपातकालीन स्थितियों के लिए तैयार होने, प्रतिक्रिया देने और पुनर्प्राप्त करने में मदद करती है।"
    }
  };

  function updateLanguage() {
    const dict = translations[currentLang];
    if (!dict) return;

    document.querySelector("a[href='#home']").textContent = dict.home;
    document.querySelector("a[href='#report']").textContent = dict.report;
    document.querySelector("a[href='#donation']").textContent = dict.donation;
    document.querySelector("a[href='#register']").textContent = dict.register;
    document.querySelector("a[href='#login']").textContent = dict.login;
    document.querySelector("a[href='#contact']").textContent = dict.contact;
    document.querySelector("a[href='#feedback']").textContent = dict.feedback;

    const alertBox = document.querySelector(".alert-box p");
    if (alertBox) alertBox.textContent = dict.alert;

    const aboutTitle = document.querySelector(".about h2");
    const aboutText = document.querySelector(".about p");
    if (aboutTitle) aboutTitle.textContent = dict.aboutTitle;
    if (aboutText) aboutText.textContent = dict.aboutText;
  }

  if (langToggle) {
    langToggle.addEventListener("click", () => {
      currentLang = currentLang === "en" ? "hi" : "en";
      updateLanguage();
      langToggle.textContent = currentLang === "en" ? "🌐" : "🇮🇳";
    });
  }

  // ===============================
  // Form Handling (Simulation)
  // ===============================
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", e => {
      e.preventDefault();
      alert("✅ Registration form submitted! (Backend integration pending)");
    });
  }

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", e => {
      e.preventDefault();
      alert("🔐 Login attempt! (Backend integration pending)");
    });
  }

});
>>>>>>> 5b60f46890df619482c3f4e7eecae82ae9792459
