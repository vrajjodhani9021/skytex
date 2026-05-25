document.addEventListener("DOMContentLoaded", async () => {
  initReviewsSection("reviews-container");

  const mapEl = document.getElementById("home-map");
  const detailsEl = document.getElementById("home-company-details");
  if (mapEl) {
    mapEl.innerHTML = `<iframe src="${SITE_CONFIG.mapEmbedUrl}" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Sky Tex location"></iframe>`;
  }
  if (detailsEl) {
    detailsEl.innerHTML = companyDetailsHtml();
  }

  const grid = document.getElementById("bestsellers-grid");
  if (!grid) return;

  try {
    const fabrics = await fetchFabrics();
    const top = fabrics.slice(0, 4);
    grid.innerHTML = top.map(productCardHtml).join("");
  } catch {
    grid.innerHTML = '<p class="empty-state">Start the Python server to see fabrics.</p>';
  }
});
