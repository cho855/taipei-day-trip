/* Part 4 JWT */

const navAuthEl =
  document.querySelector("#nav-auth") ||
  document.querySelector(".nav-right .nav-btn");

const TOKEN_KEY = "token";


function bindAuthModalEvents(overlay) {
  if (!overlay || overlay.dataset.bound === "1") return;
  overlay.dataset.bound = "1";


  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeAuthModal();
  });


  overlay.querySelector(".auth-close")?.addEventListener("click", closeAuthModal);


  overlay.querySelector("#to-signup")?.addEventListener("click", (e) => {
    e.preventDefault();
    showSignupForm();
  });

  overlay.querySelector("#to-signin")?.addEventListener("click", (e) => {
    e.preventDefault();
    showSigninForm();
  });


  overlay.querySelector("#form-signup")?.addEventListener("submit", onSubmitSignup);
  overlay.querySelector("#form-signin")?.addEventListener("submit", onSubmitSignin);
}


function ensureAuthModal() {
  let overlay = document.querySelector("#auth-overlay");


  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "auth-overlay";
    overlay.className = "auth-overlay";

    overlay.innerHTML = `
      <div class="auth-dialog is-signin" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <div class="auth-topbar"></div>

        <button type="button" class="auth-close" aria-label="close">
          <img src="/static/images/icon_close.png" alt="close" />
        </button>

        <div class="auth-body">
          <h3 id="auth-title" class="auth-title">登入會員帳號</h3>

          <form id="form-signin">
            <input id="signin-email" class="auth-input" type="email" placeholder="輸入 Email" required />
            <input id="signin-password" class="auth-input" type="password" placeholder="輸入密碼" required />
            <button type="submit" class="auth-primary-btn">登入帳戶</button>

            <div id="auth-msg" class="auth-msg"></div>

            <div class="auth-switch">
              還沒有帳戶？<a href="#" id="to-signup" class="auth-link">點此註冊</a>
            </div>
          </form>

          <form id="form-signup" style="display:none;">
            <input id="signup-name" class="auth-input" type="text" placeholder="輸入姓名" required />
            <input id="signup-email" class="auth-input" type="email" placeholder="輸入 Email" required />
            <input id="signup-password" class="auth-input" type="password" placeholder="輸入密碼" required />
            <button type="submit" class="auth-primary-btn">註冊帳戶</button>

            <div id="auth-msg2" class="auth-msg"></div>

            <div class="auth-switch">
              已經有帳戶？<a href="#" id="to-signin" class="auth-link">點此登入</a>
            </div>
          </form>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
  }

  bindAuthModalEvents(overlay);
  return overlay;
}

function openAuthModal() {
  
  document.querySelector("#category-panel")?.classList.add("hidden");

  const overlay = ensureAuthModal();
  clearAuthMsg();
  showSigninForm();
  overlay.style.display = "flex";
}

function closeAuthModal() {
  const el = document.querySelector("#auth-overlay");
  if (el) el.style.display = "none";
}

function setAuthMsg(text, isError = false) {

  const signinForm = document.querySelector("#form-signin");
  const signupForm = document.querySelector("#form-signup");
  const activeForm = signupForm?.style.display === "block" ? signupForm : signinForm;

  const msgEl =
    activeForm?.querySelector(".auth-msg") ||
    document.querySelector("#auth-msg") ||
    document.querySelector("#auth-msg2");

  if (!msgEl) return;

  msgEl.textContent = text;
  msgEl.classList.remove("error", "success");

  if (!text) return;
  msgEl.classList.add(isError ? "error" : "success");
}

function clearAuthMsg() {
  setAuthMsg("", false);
}

function showSigninForm(keepMsg = false) {
  document.querySelector("#auth-title").textContent = "登入會員帳號";
  document.querySelector("#form-signin").style.display = "block";
  document.querySelector("#form-signup").style.display = "none";

  const dialog = document.querySelector(".auth-dialog");
  if (dialog) {
    dialog.classList.add("is-signin");
    dialog.classList.remove("is-signup");
  }

  if (!keepMsg) clearAuthMsg();
}

function showSignupForm(keepMsg = false) {
  document.querySelector("#auth-title").textContent = "註冊會員帳號";
  document.querySelector("#form-signin").style.display = "none";
  document.querySelector("#form-signup").style.display = "block";

  const dialog = document.querySelector(".auth-dialog");
  if (dialog) {
    dialog.classList.add("is-signup");
    dialog.classList.remove("is-signin");
  }

  if (!keepMsg) clearAuthMsg();
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiGetMe() {
  const token = getToken();
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch("/api/user/auth", { headers });
  return res.json();
}

async function apiSignup(name, email, password) {
  const res = await fetch("/api/user", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  return { ok: res.ok, data };
}

async function apiSignin(email, password) {
  const res = await fetch("/api/user/auth", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  return { ok: res.ok, data };
}

function renderNavAuth(user) {
  if (!navAuthEl) return;

  if (!user) {
    navAuthEl.textContent = "登入/註冊";
    navAuthEl.style.cursor = "pointer";
    navAuthEl.onclick = () => openAuthModal();
  } else {
    navAuthEl.textContent = "登出系統";
    navAuthEl.style.cursor = "pointer";
    navAuthEl.onclick = () => {
      clearToken();
      location.reload();
    };
  }
}

async function onSubmitSignup(e) {
  e.preventDefault();
  clearAuthMsg();

  const name = document.querySelector("#signup-name").value.trim();
  const email = document.querySelector("#signup-email").value.trim();
  const password = document.querySelector("#signup-password").value;

  if (!name || !email || !password) {
    setAuthMsg("請填寫姓名 / Email / 密碼", true);
    return;
  }

  const result = await apiSignup(name, email, password);
  if (result.ok && result.data && result.data.ok) {
    setAuthMsg("註冊成功，請登入", false);
    showSigninForm(true);
    document.querySelector("#signin-email").value = email;
    document.querySelector("#signin-password").value = "";
  } else {
    setAuthMsg(result.data?.message || "註冊失敗", true);
  }
}

async function onSubmitSignin(e) {
  e.preventDefault();
  clearAuthMsg();

  const email = document.querySelector("#signin-email").value.trim();
  const password = document.querySelector("#signin-password").value;

  if (!email || !password) {
    setAuthMsg("請輸入 Email 與密碼", true);
    return;
  }

  const result = await apiSignin(email, password);
  if (result.ok && result.data && result.data.token) {
    setToken(result.data.token);
    setAuthMsg("登入成功", false);
    setTimeout(() => location.reload(), 500);
  } else {
    setAuthMsg(result.data?.message || "登入失敗", true);
  }
}

async function initAuth() {
  ensureAuthModal();

  try {
    const me = await apiGetMe();
    renderNavAuth(me.data);

    if (me.data === null && getToken()) {
      clearToken();
    }
  } catch (err) {
    console.error("initAuth failed:", err);
    renderNavAuth(null);
  }
}


document.addEventListener("DOMContentLoaded", initAuth);


window.initAuth = initAuth;
