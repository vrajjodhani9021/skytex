document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("contact-form");
  if (!form) return;

  const successEl = document.getElementById("contact-success");

  function showError(field, message) {
    const err = form.querySelector(`[data-error-for="${field}"]`);
    if (err) err.textContent = message;
    const input = form.querySelector(`[name="${field}"]`);
    if (input) input.classList.toggle("is-invalid", Boolean(message));
  }

  function clearErrors() {
    form.querySelectorAll("[data-error-for]").forEach((el) => (el.textContent = ""));
    form.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    clearErrors();
    let valid = true;

    const name = form.name.value.trim();
    const phone = form.phone.value.trim();
    const email = form.email.value.trim();
    const subject = form.subject.value.trim();
    const message = form.message.value.trim();

    if (!name) {
      showError("name", "Name is required");
      valid = false;
    }
    if (!phone) {
      showError("phone", "Phone number is required");
      valid = false;
    }
    if (!email) {
      showError("email", "Email is required");
      valid = false;
    } else if (!isValidEmail(email)) {
      showError("email", "Enter a valid email address");
      valid = false;
    }
    if (!subject) {
      showError("subject", "Subject is required");
      valid = false;
    }
    if (!message) {
      showError("message", "Message is required");
      valid = false;
    }

    if (!valid) return;

    form.classList.add("hidden");
    if (successEl) {
      successEl.classList.remove("hidden");
      successEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  });
});
