// Client-side language handling for ResQNet
// Loads translations from static/lang/{code}.json, applies to elements with data-translate attribute,
// persists preference in localStorage, and syncs the navbar dropdown.

async function loadLanguage(lang) {
  try {
    const response = await fetch(`/static/lang/${lang}.json`);
    if (!response.ok) {
      throw new Error(`Failed to load language file: ${response.status}`);
    }
    const translations = await response.json();

    // Apply translations to elements with data-translate attribute
    document.querySelectorAll("[data-translate]").forEach(el => {
      const key = el.getAttribute("data-translate");
      if (translations[key]) {
        if (el.placeholder !== undefined) {
          el.placeholder = translations[key];
        } else {
          el.textContent = translations[key];
        }
      }
    });

    // Also support legacy ID-based translation for backward compatibility
    Object.keys(translations).forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        const value = translations[id];
        if (typeof value === 'string') {
          if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.placeholder !== undefined && value) {
              el.placeholder = value;
            }
          } else {
            el.textContent = value;
          }
        }
      }
    });

    localStorage.setItem("selectedLang", lang);
  } catch (error) {
    console.error("Language load error:", error);
    // Fallback to English if the requested language fails
    if (lang !== 'en') {
      await loadLanguage('en');
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const savedLang = localStorage.getItem("selectedLang") || "en";
  loadLanguage(savedLang);

  const selector = document.getElementById("language-select");
  if (selector) {
    selector.value = savedLang;
    selector.addEventListener("change", e => loadLanguage(e.target.value));
  }
});



