document.addEventListener('click', async (event) => {
  const shareButton = event.target.closest('[data-catalog-share="1"]');
  if (!shareButton) return;

  const title = shareButton.dataset.shareTitle || document.title;
  const text = shareButton.dataset.shareText || title;
  const url = shareButton.dataset.shareUrl || window.location.href;

  try {
    if (navigator.share) {
      await navigator.share({ title, text, url });
      return;
    }
    await navigator.clipboard.writeText(url);
    const original = shareButton.innerHTML;
    shareButton.innerHTML = '<i class="bi bi-check2 me-1"></i>Copiado';
    window.setTimeout(() => {
      shareButton.innerHTML = original;
    }, 1500);
  } catch (error) {
    window.prompt('Copia este enlace:', url);
  }
});

document.addEventListener('click', (event) => {
  const quickViewButton = event.target.closest('[data-product-quick-view]');
  if (!quickViewButton || !window.bootstrap) return;

  const modalContent = document.querySelector('[data-product-modal-content]');
  if (!modalContent) return;
  const product = quickViewButton.dataset;
  modalContent.innerHTML = `
    <div class="row g-4 align-items-start">
      <div class="col-md-6"><div class="product-quick-image"><img src="${product.productImage}" alt="${product.productName}"></div></div>
      <div class="col-md-6"><span class="product-album" style="background:${product.productColor}">${product.productAlbum}</span>
        <h2 class="h3 fw-bold mt-3">${product.productName}</h2><p class="product-summary">${product.productDescription}</p>
        <div class="product-quick-price">${product.productPrice}</div>
        <div class="d-grid gap-2 mt-4"><a class="btn btn-success rounded-pill" href="${product.productWhatsapp}" target="_blank" rel="noopener"><i class="bi bi-whatsapp me-1"></i>Pedir por WhatsApp</a>
          <a class="btn btn-outline-primary rounded-pill" href="${product.productUrl}">Ver en página completa</a>
          <button type="button" class="btn btn-light rounded-pill" data-bs-dismiss="modal">Volver al catálogo</button></div>
      </div></div>`;
  bootstrap.Modal.getOrCreateInstance(document.getElementById('productQuickView')).show();
});

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.querySelector('[data-catalog-search-input]');
  if (!searchInput) return;

  const productCards = [...document.querySelectorAll('[data-product-search]')];
  const albumSections = [...document.querySelectorAll('[id^="album-"]')];

  const filterProducts = () => {
    const query = searchInput.value.trim().toLocaleLowerCase();

    productCards.forEach((card) => {
      const searchableText = (card.dataset.productSearch || '').toLocaleLowerCase();
      card.hidden = Boolean(query) && !searchableText.includes(query);
    });

    albumSections.forEach((section) => {
      const cards = section.querySelectorAll('[data-product-search]');
      section.hidden = cards.length > 0 && ![...cards].some((card) => !card.hidden);
    });
  };

  searchInput.addEventListener('input', filterProducts);
});

document.addEventListener('click', (event) => {
  const thumbnail = event.target.closest('[data-product-gallery-image]');
  if (!thumbnail) return;

  const mainImage = document.querySelector('[data-product-gallery-main]');
  if (!mainImage) return;

  mainImage.src = thumbnail.dataset.productGalleryImage;
  document.querySelectorAll('[data-product-gallery-image]').forEach((item) => item.classList.remove('is-active'));
  thumbnail.classList.add('is-active');
});

document.addEventListener('DOMContentLoaded', () => {
  const revealCards = document.querySelectorAll('[data-catalog-reveal]');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealCards.forEach((card, index) => {
      card.style.setProperty('--reveal-delay', `${Math.min(index * 45, 360)}ms`);
      observer.observe(card);
    });
  } else {
    revealCards.forEach((card) => card.classList.add('is-revealed'));
  }
});

let installPrompt;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  installPrompt = event;
  const installButton = document.querySelector('[data-pwa-install]');
  if (installButton) installButton.hidden = false;
});

document.addEventListener('click', async (event) => {
  const installButton = event.target.closest('[data-pwa-install]');
  if (!installButton || !installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  installButton.hidden = true;
});

document.addEventListener('DOMContentLoaded', () => {
  const imageInput = document.querySelector('[data-product-images="1"]');
  const videoInput = document.querySelector('[data-product-video="1"]');

  if (imageInput) {
    imageInput.addEventListener('change', () => {
      if (imageInput.files.length > 4) {
        imageInput.setCustomValidity('Puedes seleccionar máximo 4 imágenes.');
      } else {
        imageInput.setCustomValidity('');
      }
      imageInput.reportValidity();
    });
  }

  if (videoInput) {
    videoInput.addEventListener('change', () => {
      videoInput.setCustomValidity('');
      const file = videoInput.files[0];
      if (!file) return;

      const preview = document.createElement('video');
      preview.preload = 'metadata';
      preview.onloadedmetadata = () => {
        URL.revokeObjectURL(preview.src);
        if (preview.duration > 10) {
          videoInput.setCustomValidity('El video debe durar máximo 10 segundos.');
          videoInput.reportValidity();
        }
      };
      preview.src = URL.createObjectURL(file);
    });
  }
});
