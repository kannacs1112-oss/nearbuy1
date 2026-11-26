document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach(el => {
    el.addEventListener("click", event => {
      if (!confirm(el.dataset.confirm)) event.preventDefault();
    });
  });
  document.querySelectorAll(".flash").forEach(el => {
    window.setTimeout(() => el.classList.add("fade"), 4500);
  });
});
