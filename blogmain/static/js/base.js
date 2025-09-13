document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("theme-toggle");
  const currentTheme = getCookie("theme");

  if (currentTheme === "dark") {
    document.body.classList.add("dark");
  }

  if (toggle) {
    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      
      // Check if we're in the middle of a form submission
      const activeForms = document.querySelectorAll('form:target');
      if (activeForms.length > 0) {
        return; // Don't change theme during form submissions
      }
      
      document.body.classList.toggle("dark");
      const newTheme = document.body.classList.contains("dark") ? "dark" : "light";
      document.cookie = "theme=" + newTheme + "; path=/; max-age=" + (60*60*24*365) + "; SameSite=Lax";
      
      // Don't reload the page - just update the theme
      // location.reload(); // REMOVED - this was causing issues
    });
  }

  function getCookie(name) {
    let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }

  // Remove the problematic form submission handler
  // This was interfering with authentication forms
  
  // Add proper error handling for authentication
  const authForms = document.querySelectorAll('form[action*="login"], form[action*="signup"], form[action*="logout"]');
  authForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      // Add loading state to prevent double submissions
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
        
        // Re-enable after 5 seconds as fallback
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }, 5000);
      }
    });
  });
});

