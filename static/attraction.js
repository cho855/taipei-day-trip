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

const dateEl = document.querySelector("#date");
const priceEl = document.querySelector("#price");
const timeRadios = document.querySelectorAll('input[name="time"]');
const bookBtn = document.querySelector("#btn-booking");



let images = [];
let idx = 0;

// -------------------- helpers --------------------
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

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

function getSelectedTimeValue() {
  const checked = document.querySelector('input[name="time"]:checked');
  return checked ? checked.value : "morning";
}

function getPriceByTimeValue(timeValue) {
  return timeValue === "afternoon" ? 2500 : 2000;
}

function updatePriceByTimeValue(timeValue) {
  const price = getPriceByTimeValue(timeValue);
  if (priceEl) priceEl.textContent = `新台幣 ${price} 元`;
}

function initTimePricing() {
  if (!priceEl || !timeRadios || timeRadios.length === 0) return;

  updatePriceByTimeValue(getSelectedTimeValue());

  timeRadios.forEach((r) => {
    r.addEventListener("change", (e) => {
      updatePriceByTimeValue(e.target.value);
    });
  });
}

// -------------------- slideshow indicator --------------------
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

// -------------------- API: load attraction --------------------
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

// -------------------- Week5 Part 5-4: create booking --------------------
async function apiGetMeWithToken() {
  const token = getToken();
  if (!token) return { data: null };

  const res = await fetch("/api/user/auth", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json(); // {data: user|null}
}

async function apiCreateBooking(attractionId, date, time, price) {
  const token = getToken();
  const res = await fetch("/api/booking", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ attractionId, date, time, price }),
  });

  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function onClickBooking() {
  // 1) 檢查登入：沒登入就開彈窗
  const me = await apiGetMeWithToken();
  if (!me || !me.data) {
    // openAuthModal 是你 auth.js 已經有的函式
    if (typeof openAuthModal === "function") openAuthModal();
    return;
  }

  // 2) 準備 booking 資料
  const attractionId = getAttractionIdFromPath();
  if (!attractionId) {
    alert("景點不存在，無法預訂");
    return;
  }

  const date = dateEl ? dateEl.value : "";
  if (!date) {
    alert("請先選擇日期");
    return;
  }

  const time = getSelectedTimeValue();
  const price = getPriceByTimeValue(time);

  // 3) 打 POST /api/booking
  if (bookBtn) bookBtn.disabled = true;

  try {
    const result = await apiCreateBooking(attractionId, date, time, price);

    if (result.status === 403) {
      // token 過期或未授權
      localStorage.removeItem(TOKEN_KEY);
      if (typeof openAuthModal === "function") openAuthModal();
      return;
    }

    if (!result.ok) {
      alert(result.data?.message || "預訂失敗，請稍後再試");
      return;
    }

    // 4) 成功 → 導去 /booking
    location.href = "/booking";
  } catch (err) {
    alert("預訂失敗，請稍後再試");
  } finally {
    if (bookBtn) bookBtn.disabled = false;
  }
}

// -------------------- events --------------------
if (btnPrev) btnPrev.addEventListener("click", prev);
if (btnNext) btnNext.addEventListener("click", next);

window.addEventListener("resize", () => {
  updateIndicator();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") prev();
  if (e.key === "ArrowRight") next();
});

if (bookBtn) {
  bookBtn.addEventListener("click", onClickBooking);
}


window.addEventListener("load", async () => {
  // 不要讓 initAuth 失敗就中斷後面渲染
  try {
    if (window.initAuth) await window.initAuth();
  } catch (e) {
    console.warn("initAuth failed but continue:", e);
  }

  try {
    initTimePricing();
  } catch (e) {
    console.warn("initTimePricing failed:", e);
  }

  try {
    await loadAttraction();
  } catch (e) {
    console.error("loadAttraction failed:", e);
  }
});
