
const mainImg = document.querySelector("#main-image");
const btnPrev = document.querySelector("#img-prev");
const btnNext = document.querySelector("#img-next");
const dotsEl = document.querySelector("#dots");

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


function updatePriceByTimeValue(timeValue) {
  // morning => 2000, afternoon => 2500
  const price = timeValue === "afternoon" ? 2500 : 2000;
  priceEl.textContent = `新台幣 ${price} 元`;
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


function setImage(i) {
  if (!Array.isArray(images) || images.length === 0) {
    mainImg.removeAttribute("src");
    mainImg.alt = "no image";
    dotsEl.innerHTML = "";
    btnPrev.disabled = true;
    btnNext.disabled = true;
    return;
  }

  idx = (i + images.length) % images.length;
  mainImg.src = images[idx];
  mainImg.alt = titleEl.textContent || "attraction";


  dotsEl.innerHTML = images
    .map((_, di) => `<span class="dot ${di === idx ? "active" : ""}" data-i="${di}"></span>`)
    .join("");

  btnPrev.disabled = images.length <= 1;
  btnNext.disabled = images.length <= 1;
}

function next() { setImage(idx + 1); }
function prev() { setImage(idx - 1); }

async function loadAttraction() {
  const attractionId = getAttractionIdFromPath();
  if (!attractionId) {
    titleEl.textContent = "景點不存在";
    subtitleEl.textContent = "";
    setImage(0);
    return;
  }

  let res;
  try {
    res = await fetch(`/api/attraction/${attractionId}`);
  } catch (err) {
    titleEl.textContent = "載入失敗";
    subtitleEl.textContent = "請稍後再試";
    setImage(0);
    return;
  }

  const data = await res.json();

  if (!data || !data.data) {
    titleEl.textContent = "景點不存在";
    subtitleEl.textContent = "";
    setImage(0);
    return;
  }

  const a = data.data;

  titleEl.textContent = a.name || "—";
  subtitleEl.textContent = `${a.category || ""}${a.mrt ? " at " + a.mrt : ""}`.trim();

  descEl.textContent = a.description || "";
  addressEl.textContent = a.address || "—";
  transportEl.textContent = a.transport || "—";

  images = Array.isArray(a.images) ? a.images.filter(Boolean) : [];
  setImage(0);
}


btnPrev.addEventListener("click", prev);
btnNext.addEventListener("click", next);

dotsEl.addEventListener("click", (e) => {
  const t = e.target;
  if (!t.classList.contains("dot")) return;
  const i = Number(t.dataset.i);
  if (!Number.isInteger(i)) return;
  setImage(i);
});


document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") prev();
  if (e.key === "ArrowRight") next();
});


window.addEventListener("load", () => {
  initTimePricing();
  loadAttraction();
});
