const CUSTOMER_REVIEWS = [
  {
    name: "Amelia R.",
    rating: 5,
    date: "12 Mar 2026",
    text: "The linen drapes like a dream. Sky Tex has become my go-to for every studio collection.",
    project: "Linen capsule wardrobe",
    avatar: "https://ui-avatars.com/api/?name=Amelia+R&background=8b7355&color=fff&size=128",
  },
  {
    name: "Noor S.",
    rating: 5,
    date: "28 Feb 2026",
    text: "Honest fibers, honest pricing, and the swatch kit made decision-making effortless.",
    project: "Bespoke curtains",
    avatar: "https://ui-avatars.com/api/?name=Noor+S&background=5c4a38&color=fff&size=128",
  },
  {
    name: "Camille D.",
    rating: 5,
    date: "15 Feb 2026",
    text: "Soft hand, beautiful color depth — my finished quilt looks like it belongs in a museum.",
    project: "Heirloom quilt",
    avatar: "https://ui-avatars.com/api/?name=Camille+D&background=c4a882&color=2c2824&size=128",
  },
  {
    name: "Rohan K.",
    rating: 4,
    date: "2 Feb 2026",
    text: "Fast dispatch and the silk charmeuse exceeded expectations. Will order again for bridal wear.",
    project: "Evening wear",
    avatar: "https://ui-avatars.com/api/?name=Rohan+K&background=8b7355&color=fff&size=128",
  },
  {
    name: "Priya M.",
    rating: 5,
    date: "18 Jan 2026",
    text: "Wholesale team was responsive and samples matched the online photos perfectly.",
    project: "Boutique inventory",
    avatar: "https://ui-avatars.com/api/?name=Priya+M&background=5c4a38&color=fff&size=128",
  },
  {
    name: "James T.",
    rating: 5,
    date: "5 Jan 2026",
    text: "Organic cotton poplin washed beautifully. Great communication on GSM and weight.",
    project: "Shirt collection",
    avatar: "https://ui-avatars.com/api/?name=James+T&background=c4a882&color=2c2824&size=128",
  },
];

function starsHtml(rating) {
  return Array.from({ length: 5 }, (_, i) => {
    const filled = i < rating;
    return `<span class="star${filled ? " star--filled" : ""}" aria-hidden="true">★</span>`;
  }).join("");
}

function reviewCardHtml(review) {
  return `
    <article class="review-card">
      <div class="review-card__header">
        <img class="review-card__avatar" src="${review.avatar}" alt="${review.name}" width="56" height="56" loading="lazy" />
        <div>
          <div class="review-card__stars" aria-label="${review.rating} out of 5 stars">${starsHtml(review.rating)}</div>
          <h3 class="review-card__name">${review.name}</h3>
          <time class="review-card__date" datetime="${review.date}">${review.date}</time>
        </div>
      </div>
      <p class="review-card__text">"${review.text}"</p>
      <p class="review-card__project">${review.project}</p>
    </article>
  `;
}

function getAverageRating(reviews) {
  if (!reviews.length) return { average: 0, count: 0 };
  const sum = reviews.reduce((acc, r) => acc + r.rating, 0);
  return { average: (sum / reviews.length).toFixed(1), count: reviews.length };
}

function initReviewsSection(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const { average, count } = getAverageRating(CUSTOMER_REVIEWS);

  container.innerHTML = `
    <div class="reviews-summary">
      <div class="reviews-summary__score">
        <span class="reviews-summary__number">${average}</span>
        <div class="reviews-summary__stars" aria-label="Average ${average} out of 5">${starsHtml(Math.round(Number(average)))}</div>
        <p class="reviews-summary__count">Based on ${count} customer reviews</p>
      </div>
    </div>
    <div class="reviews-carousel">
      <button type="button" class="reviews-carousel__btn reviews-carousel__btn--prev" aria-label="Previous review">‹</button>
      <div class="reviews-carousel__track" tabindex="0">${CUSTOMER_REVIEWS.map(reviewCardHtml).join("")}</div>
      <button type="button" class="reviews-carousel__btn reviews-carousel__btn--next" aria-label="Next review">›</button>
    </div>
    <div class="reviews-dots" aria-hidden="true"></div>
  `;

  const track = container.querySelector(".reviews-carousel__track");
  const prev = container.querySelector(".reviews-carousel__btn--prev");
  const next = container.querySelector(".reviews-carousel__btn--next");
  const dotsWrap = container.querySelector(".reviews-dots");
  const cards = track.querySelectorAll(".review-card");

  cards.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "reviews-dot" + (i === 0 ? " is-active" : "");
    dot.setAttribute("aria-label", `Go to review ${i + 1}`);
    dot.addEventListener("click", () => scrollToCard(i));
    dotsWrap.appendChild(dot);
  });

  function scrollToCard(index) {
    const card = cards[index];
    if (!card) return;
    track.scrollTo({ left: card.offsetLeft - track.offsetLeft, behavior: "smooth" });
    dotsWrap.querySelectorAll(".reviews-dot").forEach((d, i) => {
      d.classList.toggle("is-active", i === index);
    });
  }

  let activeIndex = 0;
  prev.addEventListener("click", () => {
    activeIndex = (activeIndex - 1 + cards.length) % cards.length;
    scrollToCard(activeIndex);
  });
  next.addEventListener("click", () => {
    activeIndex = (activeIndex + 1) % cards.length;
    scrollToCard(activeIndex);
  });

  track.addEventListener("scroll", () => {
    let closest = 0;
    let minDist = Infinity;
    cards.forEach((card, i) => {
      const dist = Math.abs(card.offsetLeft - track.scrollLeft);
      if (dist < minDist) {
        minDist = dist;
        closest = i;
      }
    });
    activeIndex = closest;
    dotsWrap.querySelectorAll(".reviews-dot").forEach((d, i) => {
      d.classList.toggle("is-active", i === closest);
    });
  });
}
