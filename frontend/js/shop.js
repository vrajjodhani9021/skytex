document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(window.location.search);
  const grid = document.getElementById("fabric-grid");
  const countEl = document.getElementById("fabric-count");
  const titleEl = document.getElementById("shop-title");

  const filters = {
    q: params.get("q") || "",
    material: params.get("material") || "",
    color: params.get("color") || "",
    use: params.get("use") || "",
  };

  if (filters.material) {
    titleEl.textContent = filters.material + " fabrics";
  } else if (filters.use) {
    titleEl.textContent = "Fabrics for " + filters.use;
  }

  document.querySelectorAll("[data-filter]").forEach((btn) => {
    const key = btn.dataset.filter;
    const value = btn.dataset.value;
    if (filters[key] === value) btn.classList.add("is-active");
    btn.addEventListener("click", () => {
      if (filters[key] === value) {
        params.delete(key);
      } else {
        params.set(key, value);
      }
      window.location.search = params.toString();
    });
  });

  const searchInput = document.getElementById("search-input");
  if (searchInput && filters.q) searchInput.value = filters.q;
  searchInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      if (searchInput.value) params.set("q", searchInput.value);
      else params.delete("q");
      window.location.search = params.toString();
    }
  });

  try {
    const fabrics = await fetchFabrics(filters);
    countEl.textContent = fabrics.length + " fabric" + (fabrics.length === 1 ? "" : "s");
    if (fabrics.length === 0) {
      grid.innerHTML = '<p class="empty-state">No fabrics match your filters.</p>';
      return;
    }
    grid.innerHTML = fabrics.map(productCardHtml).join("");
  } catch {
    grid.innerHTML = '<p class="empty-state">Could not load fabrics. Is the server running?</p>';
  }
});
