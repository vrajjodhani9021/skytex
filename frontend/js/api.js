const API_BASE = "";

function formatPrice(inr) {
  return "₹" + Number(inr).toLocaleString("en-IN") + "/meter";
}

async function fetchFabrics(params = {}) {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.material) query.set("material", params.material);
  if (params.color) query.set("color", params.color);
  if (params.use) query.set("use", params.use);

  const url = API_BASE + "/api/fabrics" + (query.toString() ? "?" + query : "");
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to load fabrics");
  return res.json();
}

async function fetchFabric(slug) {
  const res = await fetch(API_BASE + "/api/fabrics/" + encodeURIComponent(slug));
  if (!res.ok) throw new Error("Fabric not found");
  return res.json();
}

function productCardHtml(fabric) {
  return `
    <article class="product-card">
      <a href="product.html?slug=${fabric.slug}" class="product-card__image-wrap">
        <img src="${fabric.image_url}" alt="${fabric.name}" loading="lazy" />
        <div class="product-card__overlay">
          <span class="btn btn--ghost btn--sm">View</span>
        </div>
      </a>
      <div class="product-card__body">
        <a href="product.html?slug=${fabric.slug}" class="product-card__title">${fabric.name}</a>
        <p class="product-card__meta">(${fabric.reviews_count})</p>
        <p class="product-card__price">${formatPrice(fabric.price_inr)}</p>
      </div>
    </article>
  `;
}
