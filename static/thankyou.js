
(function () {
  const el = document.querySelector("#order-number");
  const hint = document.querySelector("#hint");

  function getOrderNumber() {
    const params = new URLSearchParams(window.location.search);
    return (params.get("number") || "").trim();
  }

  const number = getOrderNumber();

  if (!el) return;

  if (number === "") {
    el.textContent = "找不到訂單編號";
    if (hint) {
      hint.textContent = "網址缺少 ?number=xxxx，請確認是從付款流程導向過來。";
    }
  } else {
    el.textContent = number;
  }

  const btnHome = document.querySelector("#btn-home");
  const btnBooking = document.querySelector("#btn-booking");

  if (btnHome) btnHome.addEventListener("click", () => (window.location.href = "/"));
  if (btnBooking) btnBooking.addEventListener("click", () => (window.location.href = "/booking"));
})();
