
function getToken() {
  return localStorage.getItem("token");
}

function clearToken() {
  localStorage.removeItem("token");
}

function authHeaders() {
  const token = getToken();
  if (!token) return null;
  return { Authorization: `Bearer ${token}` };
}

function qs(sel) {
  return document.querySelector(sel);
}

function show(el) {
  if (el) el.classList.remove("hidden");
}

function hide(el) {
  if (el) el.classList.add("hidden");
}


function formatTimeText(timeValue) {
  if (timeValue === "morning") return "早上 9 點到下午 4 點";
  if (timeValue === "afternoon") return "下午 1 點到晚上 8 點";
  return timeValue || "";
}

function formatPriceNumber(price) {
  if (price == null) return 0;
  const n = Number(price);
  return Number.isFinite(n) ? n : 0;
}


async function apiGetMe() {
  const headers = authHeaders();
  if (!headers) return { data: null };

  const res = await fetch("/api/user/auth", { headers });
  return res.json();
}

async function apiGetBooking() {
  const headers = authHeaders();
  if (!headers) return { unauthorized: true, data: null };

  const res = await fetch("/api/booking", { headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 403) return { unauthorized: true, data: null };
  if (!res.ok) throw new Error(data?.message || "取得預定行程失敗");

  return { unauthorized: false, data };
}

async function apiDeleteBooking() {
  const headers = authHeaders();
  if (!headers) return { unauthorized: true, data: null };

  const res = await fetch("/api/booking", { method: "DELETE", headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 403) return { unauthorized: true, data: null };
  if (!res.ok) throw new Error(data?.message || "刪除失敗");

  return { unauthorized: false, data };
}


function renderEmptyState(me) {
  const nameEl = qs("#member-name");
  if (nameEl) nameEl.textContent = me?.name || "—";

  const emptyEl = qs("#empty-state");
  const bookingSection = qs("#booking-section");

  show(emptyEl);
  hide(bookingSection);

  hide(qs("#contact-section"));
  hide(qs("#payment-section"));
  hide(qs("#checkout-section"));


  document.querySelectorAll(".divider").forEach((hr) => hr.classList.add("hidden"));

  const totalEl = qs("#total-price");
  if (totalEl) totalEl.textContent = "0";
}


function renderBookingState(me, booking) {

  const nameEl = qs("#member-name");
  if (nameEl) nameEl.textContent = me?.name || "—";


  hide(qs("#empty-state"));
  show(qs("#booking-section"));


  show(qs("#contact-section"));
  show(qs("#payment-section"));
  show(qs("#checkout-section"));


  document.querySelectorAll(".divider").forEach((hr) => hr.classList.remove("hidden"));


  const a = booking?.attraction || {};

  const imgEl = qs("#booking-image");
  if (imgEl) {
    imgEl.src = a.image || "";
    imgEl.alt = a.name || "attraction";
  }

  const titleEl = qs("#booking-title");
  if (titleEl) {
    titleEl.textContent = `台北一日遊：${a.name || "—"}`;
    if (a.id) titleEl.href = `/attraction/${a.id}`;
  }

  const dateEl = qs("#booking-date");
  if (dateEl) dateEl.textContent = booking?.date || "—";

  const timeEl = qs("#booking-time");
  if (timeEl) timeEl.textContent = formatTimeText(booking?.time);

  const priceEl = qs("#booking-price");
  const priceNum = formatPriceNumber(booking?.price);
  if (priceEl) priceEl.textContent = `新台幣 ${priceNum} 元`;

  const addrEl = qs("#booking-address");
  if (addrEl) addrEl.textContent = a.address || "—";

  
  const totalEl = qs("#total-price");
  if (totalEl) totalEl.textContent = String(priceNum);


  const cName = qs("#contact-name");
  const cEmail = qs("#contact-email");
  if (cName) cName.value = me?.name || "";
  if (cEmail) cEmail.value = me?.email || "";
}

function bindDeleteButton() {
  const delBtn = qs("#delete-booking"); 
  if (!delBtn) {
    console.warn("Delete button not found: #delete-booking");
    return;
  }

  delBtn.addEventListener("click", async () => {
    delBtn.disabled = true;
    try {
      const result = await apiDeleteBooking();
      if (result.unauthorized) {
        clearToken();
        location.href = "/";
        return;
      }
      location.reload();
    } catch (err) {
      alert(err?.message || "刪除失敗");
      delBtn.disabled = false;
    }
  });
}


async function initBookingPage() {

  let me;
  try {
    me = await apiGetMe();
  } catch (err) {
    location.href = "/";
    return;
  }

  if (!me || !me.data) {
    location.href = "/";
    return;
  }


  try {
    const result = await apiGetBooking();

    if (result.unauthorized) {
      clearToken();
      location.href = "/";
      return;
    }

    const booking = result?.data?.data;

    if (!booking) {
      renderEmptyState(me.data);
      return;
    }

    renderBookingState(me.data, booking);
    bindDeleteButton();
  } catch (err) {
    console.error("initBookingPage error:", err);
    renderEmptyState(me?.data);
  }
}

document.addEventListener("DOMContentLoaded", initBookingPage);
