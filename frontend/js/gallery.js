function escapeAttr(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function youtubeEmbedUrl(url) {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]+)/i);
  return match ? `https://www.youtube.com/embed/${match[1]}` : null;
}

function vimeoEmbedUrl(url) {
  const match = url.match(/vimeo\.com\/(?:video\/)?(\d+)/i);
  return match ? `https://player.vimeo.com/video/${match[1]}` : null;
}

function getFabricMedia(fabric) {
  if (fabric.media && fabric.media.length) {
    return fabric.media;
  }
  if (fabric.image_url) {
    return [{ media_type: "image", url: fabric.image_url, video_source: null, sort_order: 0 }];
  }
  return [];
}

function mediaThumbnailHtml(item, index, isActive) {
  if (item.media_type === "video") {
    const isEmbed = item.video_source === "youtube" || item.video_source === "vimeo";
    const thumbSrc = isEmbed
      ? "https://ivory-weave-emporium.lovable.app/assets/cat-silk-BJp8dj0T.jpg"
      : item.url;
    return `
      <button type="button" class="gallery-thumb gallery-thumb--video${isActive ? " is-active" : ""}" data-index="${index}" aria-label="View video">
        <img src="${thumbSrc}" alt="" />
        <span class="gallery-thumb__play" aria-hidden="true">▶</span>
      </button>
    `;
  }
  return `
    <button type="button" class="gallery-thumb${isActive ? " is-active" : ""}" data-index="${index}" aria-label="View image ${index + 1}">
      <img src="${item.url}" alt="" />
    </button>
  `;
}

function mediaMainHtml(item) {
  if (item.media_type === "video") {
    if (item.video_source === "youtube") {
      const embed = youtubeEmbedUrl(item.url);
      return `<div class="gallery-main__video"><iframe src="${embed}" allowfullscreen title="Product video"></iframe></div>`;
    }
    if (item.video_source === "vimeo") {
      const embed = vimeoEmbedUrl(item.url);
      return `<div class="gallery-main__video"><iframe src="${embed}" allowfullscreen title="Product video"></iframe></div>`;
    }
    return `
      <div class="gallery-main__video">
        <video controls playsinline poster="">
          <source src="${escapeAttr(item.url)}" type="video/mp4" />
        </video>
      </div>
    `;
  }
  return `
    <button type="button" class="gallery-main__zoom" data-lightbox="${escapeAttr(item.url)}" aria-label="Open full screen image">
      <img src="${item.url}" alt="" class="gallery-main__img" />
    </button>
  `;
}

function renderProductGallery(container, fabric) {
  const media = getFabricMedia(fabric);
  if (!media.length) {
    container.innerHTML = '<p class="empty-state">No images available.</p>';
    return;
  }

  container.innerHTML = `
    <div class="product-gallery">
      <div class="gallery-main" id="gallery-main">${mediaMainHtml(media[0])}</div>
      <div class="gallery-thumbs" id="gallery-thumbs">
        ${media.map((m, i) => mediaThumbnailHtml(m, i, i === 0)).join("")}
      </div>
    </div>
  `;

  const mainEl = container.querySelector("#gallery-main");
  const thumbs = container.querySelectorAll(".gallery-thumb");

  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", () => {
      const index = Number(thumb.dataset.index);
      const item = media[index];
      mainEl.innerHTML = mediaMainHtml(item);
      thumbs.forEach((t) => t.classList.toggle("is-active", t === thumb));
      bindLightboxTriggers(container);
    });
  });

  bindLightboxTriggers(container);
}

let lightboxEl = null;

function ensureLightbox() {
  if (lightboxEl) return lightboxEl;
  lightboxEl = document.createElement("div");
  lightboxEl.className = "lightbox hidden";
  lightboxEl.innerHTML = `
    <div class="lightbox__backdrop" data-close></div>
    <div class="lightbox__content">
      <button type="button" class="lightbox__close" data-close aria-label="Close">×</button>
      <div class="lightbox__body"></div>
    </div>
  `;
  document.body.appendChild(lightboxEl);
  lightboxEl.querySelectorAll("[data-close]").forEach((el) => {
    el.addEventListener("click", closeLightbox);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });
  return lightboxEl;
}

function openLightbox(url) {
  const lb = ensureLightbox();
  lb.querySelector(".lightbox__body").innerHTML = `<img src="${escapeAttr(url)}" alt="Full size product image" />`;
  lb.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  if (!lightboxEl) return;
  lightboxEl.classList.add("hidden");
  document.body.style.overflow = "";
}

function bindLightboxTriggers(container) {
  container.querySelectorAll("[data-lightbox]").forEach((btn) => {
    btn.addEventListener("click", () => openLightbox(btn.dataset.lightbox));
  });
}
