
const mainImg = document.querySelector("#main-image");
const btnPrev = document.querySelector("#img-prev");
const btnNext = document.querySelector("#img-next");
const dotsEl = document.querySelector("#dots");
const indicatorEl = document.querySelector("#indicator-active");

const titleEl = document.querySelector("#title");
const subtitleEl = document.querySelector("#subtitle");
const descEl = document.querySelector("#desc");
const addressEl = document.querySelector("#address");
const transportEl = document.querySelector("#transport");

const priceEl = document.querySelector("#price");
const timeRadios = document.querySelectorAll('input[name="time"]');

let images = [];
let idx = 0;


function getAttractionIdFromPath() {
  const parts = location.pathname.split("/").filter(Boolean);
  const last = parts[parts.length - 1];
  const n = Number(last);
  return Number.isInteger(n) && n > 0 ? n : null;
}

function clampIndex(i, len) {
  if (len <= 0) return 0;
  return (i + len) % len;
}


function updatePriceByTimeValue(timeValue) {
  const price = timeValue === "afternoon" ? 2500 : 2000;
  if (priceEl) priceEl.textContent = `新台幣 ${price} 元`;
}

function initTimePricing() {
  if (!priceEl || !timeRadios || timeRadios.length === 0) return;

  const checked = document.querySelector('input[name="time"]:checked');
  updatePriceByTimeValue(checked ? checked.value : "morning");

  timeRadios.forEach((r) => {
    r.addEventListener("change", (e) => {
      updatePriceByTimeValue(e.target.value);
    });
  });
}


function updateIndicator() {
  if (!dotsEl || !indicatorEl) return;

  const len = images.length;
  if (len <= 0) {
    indicatorEl.style.width = "0px";
    indicatorEl.style.transform = "translateX(0px)";
    return;
  }


  const trackW = dotsEl.clientWidth;    
  const segW = trackW / len;
  const x = segW * idx;

  indicatorEl.style.width = `${segW}px`;
  indicatorEl.style.transform = `translateX(${x}px)`;
}


function setImage(i) {
  const len = images.length;

  if (!Array.isArray(images) || len === 0) {
    if (mainImg) {
      mainImg.removeAttribute("src");
      mainImg.alt = "no image";
    }
    if (btnPrev) btnPrev.disabled = true;
    if (btnNext) btnNext.disabled = true;
    if (indicatorEl) {
      indicatorEl.style.width = "0px";
      indicatorEl.style.transform = "translateX(0px)";
    }
    return;
  }

  idx = clampIndex(i, len);

  mainImg.src = images[idx];
  mainImg.alt = (titleEl && titleEl.textContent) ? titleEl.textContent : "attraction";

  if (btnPrev) btnPrev.disabled = len <= 1;
  if (btnNext) btnNext.disabled = len <= 1;

  updateIndicator();
}

function next() { setImage(idx + 1); }
function prev() { setImage(idx - 1); }


async function loadAttraction() {
  const attractionId = getAttractionIdFromPath();
  if (!attractionId) {
    if (titleEl) titleEl.textContent = "景點不存在";
    if (subtitleEl) subtitleEl.textContent = "";
    images = [];
    setImage(0);
    return;
  }

  let res;
  try {
    res = await fetch(`/api/attraction/${attractionId}`);
  } catch (err) {
    if (titleEl) titleEl.textContent = "載入失敗";
    if (subtitleEl) subtitleEl.textContent = "請稍後再試";
    images = [];
    setImage(0);
    return;
  }

  if (!res.ok) {
    if (titleEl) titleEl.textContent = "景點不存在";
    if (subtitleEl) subtitleEl.textContent = "";
    images = [];
    setImage(0);
    return;
  }

  const payload = await res.json();
  if (!payload || !payload.data) {
    if (titleEl) titleEl.textContent = "景點不存在";
    if (subtitleEl) subtitleEl.textContent = "";
    images = [];
    setImage(0);
    return;
  }

  const a = payload.data;

  if (titleEl) titleEl.textContent = a.name || "—";
  if (subtitleEl) {
    subtitleEl.textContent = `${a.category || ""}${a.mrt ? " at " + a.mrt : ""}`.trim() || "—";
  }

  if (descEl) descEl.textContent = a.description || "";
  if (addressEl) addressEl.textContent = a.address || "—";
  if (transportEl) transportEl.textContent = a.transport || "—";

  images = Array.isArray(a.images) ? a.images.filter(Boolean) : [];
  setImage(0);


  requestAnimationFrame(updateIndicator);
}


if (btnPrev) btnPrev.addEventListener("click", prev);
if (btnNext) btnNext.addEventListener("click", next);


window.addEventListener("resize", () => {
  updateIndicator();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") prev();
  if (e.key === "ArrowRight") next();
});


window.addEventListener("load", () => {
  initTimePricing();
  loadAttraction();
});
