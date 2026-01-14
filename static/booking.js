
function getToken() {
  return localStorage.getItem("token");
}

function clearToken() {
  localStorage.removeItem("token");
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
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
  if (!headers.Authorization) return { data: null };
  const res = await fetch("/api/user/auth", { headers });
  return res.json();
}

async function apiGetBooking() {
  const headers = authHeaders();
  if (!headers.Authorization) return { unauthorized: true, data: null };

  const res = await fetch("/api/booking", { headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 403) return { unauthorized: true, data: null };
  if (!res.ok) throw new Error(data?.message || "取得預定行程失敗");

  return { unauthorized: false, data };
}

async function apiDeleteBooking() {
  const headers = authHeaders();
  if (!headers.Authorization) return { unauthorized: true, data: null };

  const res = await fetch("/api/booking", { method: "DELETE", headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 403) return { unauthorized: true, data: null };
  if (!res.ok) throw new Error(data?.message || "刪除失敗");

  return { unauthorized: false, data };
}

function renderEmptyState(me) {
  const nameEl = qs("#member-name");
  if (nameEl) nameEl.textContent = me?.name || "—";

  show(qs("#empty-state"));
  hide(qs("#booking-section"));

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

  const priceNum = formatPriceNumber(booking?.price);
  const priceEl = qs("#booking-price");
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
  if (!delBtn) return;

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


function setPayEnabled(btn, enabled) {
  if (!btn) return;
  btn.disabled = !enabled;
  if (enabled) btn.removeAttribute("disabled");
  else btn.setAttribute("disabled", "disabled");
  btn.style.opacity = enabled ? "1" : "0.6";
  btn.style.cursor = enabled ? "pointer" : "not-allowed";
}

function ensureTapPayReady() {
  return typeof TPDirect !== "undefined" && TPDirect.card;
}

function setupTapPayCardFields() {
  if (window.__tappay_card_setup_done) return;
  window.__tappay_card_setup_done = true;

  TPDirect.card.setup({
    fields: {
      number: {
        element: "#card-number",
        placeholder: "**** **** **** ****",
      },
      expirationDate: {
        element: "#card-expiration-date",
        placeholder: "MM / YY",
      },
      ccv: {
        element: "#card-ccv",
        placeholder: "CCV",
      },
    },
    styles: {
      input: {
        "font-size": "16px",
        color: "#000",
      },
      ":focus": { color: "#000" },
      ".valid": { color: "#000" },
      ".invalid": { color: "#d9534f" },
    },
  });
}

let gBookingForOrder = null;

async function initBookingPage() {
  let me;
  try {
    me = await apiGetMe();
  } catch {
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
      gBookingForOrder = null;
      renderEmptyState(me.data);
      return;
    }

    gBookingForOrder = booking;
    renderBookingState(me.data, booking);
    bindDeleteButton();
  } catch (err) {
    console.error("initBookingPage error:", err);
    gBookingForOrder = null;
    renderEmptyState(me?.data);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await initBookingPage();

  const payBtn = qs("#pay-btn");
  if (!payBtn) return;

 
  setPayEnabled(payBtn, false);

  if (!ensureTapPayReady()) {
    alert("TapPay SDK 尚未載入，請確認 booking.html 已載入 TapPay script。");
    return;
  }


  try {
    TPDirect.setupSDK(window.TAPPAY_APP_ID, window.TAPPAY_APP_KEY, window.TAPPAY_ENV || "sandbox");
  } catch (e) {
 
  }

  setupTapPayCardFields();

 
  TPDirect.card.onUpdate((update) => {
    setPayEnabled(payBtn, !!update.canGetPrime);
  });


  payBtn.addEventListener("click", async (e) => {
    e.preventDefault();

   
    if (!gBookingForOrder) {
      alert("目前沒有可付款的預定行程");
      return;
    }

   
    const token = getToken();
    if (!token) {
      alert("請先登入會員");
      return;
    }

 
    const contactName = (qs("#contact-name")?.value || "").trim();
    const contactEmail = (qs("#contact-email")?.value || "").trim();
    const contactPhone = (qs("#contact-phone")?.value || "").trim();

    if (!contactName || !contactEmail || !contactPhone) {
      alert("聯絡資訊不可空白");
      return;
    }

   
    const status = TPDirect.card.getTappayFieldsStatus();
    if (!status || status.canGetPrime !== true) {
      alert("信用卡資訊尚未填寫完整或格式不正確");
      return;
    }

    
    setPayEnabled(payBtn, false);

    
    TPDirect.card.getPrime(async (primeResult) => {
      if (!primeResult || primeResult.status !== 0) {
        alert("取得 Prime 失敗，請確認信用卡資訊");
        setPayEnabled(payBtn, true);
        return;
      }

      const prime = primeResult.card.prime;

      
      try {
        const resp = await fetch("/api/orders", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders(),
          },
          body: JSON.stringify({
            prime,
            contact: {
              name: contactName,
              email: contactEmail,
              phone: contactPhone,
            },
          }),
        });

        const result = await resp.json().catch(() => ({}));

        
        if (resp.status === 403) {
          clearToken();
          alert("登入已過期，請重新登入");
          location.href = "/";
          return;
        }

        if (!resp.ok) {
          alert(result.message || "訂單建立失敗");
          setPayEnabled(payBtn, true);
          return;
        }

        
        const data = result.data;
        if (!data || !data.payment) {
          alert(result.message || "訂單建立失敗");
          setPayEnabled(payBtn, true);
          return;
        }

        const { number, payment } = data;

        
        if (payment.status === 0) {
          window.location.href = `/thankyou?number=${number}`;
        } else {
          alert(`付款失敗：${payment.message} (status=${payment.status})`);
          setPayEnabled(payBtn, true);
        }
      } catch (err) {
        console.error(err);
        alert("系統錯誤，請稍後再試");
        setPayEnabled(payBtn, true);
      }
    });
  });
});
