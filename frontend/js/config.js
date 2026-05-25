const SITE_CONFIG = {
  companyName: "Sky Tex Textile Atelier",
  address: "D-3248-49-50, Globle Textile Market, Nr. Globle textile Market, Surat (395010)",
  phone: "+91 99044 77080",
  email: "skytex035@gmail.com",
  whatsappNumber: "919904477080",
  contactPerson: "Pavan Patel",
  workingHours: "Mon–Sat: 10:00 AM – 7:00 PM · Sun: Closed",
  social: {
    instagram: "https://www.instagram.com/",
    facebook: "https://www.facebook.com/",
    pinterest: "https://www.pinterest.com/",
  },
  mapEmbedUrl:
    "https://maps.google.com/maps?q=Globale%20Textile%20Market,%20Surat&t=&z=15&ie=UTF8&iwloc=&output=embed",
  departments: {
    info: "info@skytexsurat.com",
    pavan: "pavan@skytexsurat.com",
    sales: "sales@skytexsurat.com",
    export: "export@skytexsurat.com",
  },
};

function whatsappProductLink(productName, priceInr) {
  const price = "₹" + Number(priceInr).toLocaleString("en-IN") + "/meter";
  const text = encodeURIComponent(
    `Hi, I'm interested in ${productName} priced at ${price}`
  );
  return `https://wa.me/${SITE_CONFIG.whatsappNumber}?text=${text}`;
}

function whatsappGeneralLink(message) {
  const text = encodeURIComponent(message || "Hi, I'd like to know more about your fabrics.");
  return `https://wa.me/${SITE_CONFIG.whatsappNumber}?text=${text}`;
}

function companyMapHtml(className) {
  return `<div class="${className || "map-embed"}">
    <iframe src="${SITE_CONFIG.mapEmbedUrl}" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Sky Tex location"></iframe>
  </div>`;
}

function companyDetailsHtml(options = {}) {
  const { compact = false } = options;
  const social = Object.entries(SITE_CONFIG.social)
    .map(
      ([name, url]) =>
        `<a href="${url}" target="_blank" rel="noopener noreferrer" class="social-link social-link--${name}">${name.charAt(0).toUpperCase() + name.slice(1)}</a>`
    )
    .join("");

  const departmentItems = Object.entries(SITE_CONFIG.departments)
    .map(
      ([dept, email]) => `
        <div class="dept-email-item">
          <span class="dept-name">${dept.charAt(0).toUpperCase() + dept.slice(1)}</span>
          <a class="dept-link" href="mailto:${email}">${email}</a>
        </div>
      `
    )
    .join("");

  return `
    <div class="company-details${compact ? " company-details--compact" : ""}">
      <h3>${SITE_CONFIG.companyName}</h3>
      
      <div class="contact-person-badge">
        <span class="badge-label">Representative</span>
        <span class="badge-name">${SITE_CONFIG.contactPerson}</span>
      </div>

      <ul class="company-details__list">
        <li><strong>Address</strong><span>${SITE_CONFIG.address}</span></li>
        <li><strong>Phone</strong><span><a href="tel:${SITE_CONFIG.phone.replace(/\s/g, "")}">${SITE_CONFIG.phone}</a> (${SITE_CONFIG.contactPerson})</span></li>
        <li><strong>General Email</strong><span><a href="mailto:${SITE_CONFIG.email}">${SITE_CONFIG.email}</a></span></li>
        <li><strong>Hours</strong><span>${SITE_CONFIG.workingHours}</span></li>
      </ul>

      <div class="company-departments">
        <h4>Department Contacts</h4>
        <div class="dept-emails-grid">
          ${departmentItems}
        </div>
      </div>

      <div class="company-details__social">${social}</div>
    </div>
  `;
}
