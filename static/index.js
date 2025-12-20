const listEl = document.querySelector("#attraction-list");
const sentinel = document.querySelector("#sentinel");

const categoryBtn = document.querySelector("#category-btn");
const categoryPanel = document.querySelector("#category-panel");
const categoryList = document.querySelector("#category-list");
const categoryText = document.querySelector("#category-text");

const keywordInput = document.querySelector("#keyword-input");
const searchBtn = document.querySelector("#search-btn");

const mrtList = document.querySelector("#mrt-list");
const mrtScroll = document.querySelector(".mrt-scroll");

const mrtLeft = document.querySelector("#mrt-left");
const mrtRight = document.querySelector("#mrt-right");

let nextPage = 0;
let isLoading = false;
let currentKeyword = "";
let currentCategory = "";


function buildURL(page) {
  const url = new URL("/api/attractions", location.origin);
  url.searchParams.set("page", page);
  if (currentKeyword) url.searchParams.set("keyword", currentKeyword);
  if (currentCategory) url.searchParams.set("category", currentCategory);
  return url;
}

function render(attractions, append) {
  const html = attractions.map(a => {
    const img = (a.images && a.images.length) ? a.images[0] : "";
    const mrt = a.mrt || "";
    const cat = a.category || "";

    return `
      <a class="card-link" href="/attraction/${a.id}">
        <div class="attraction-card">
          <div class="pic" style="background-image: url('${img}')">
            <div class="title-bar">
              <div class="title">${a.name}</div>
            </div>
          </div>
          <div class="meta">
            <div class="mrt">${mrt}</div>
            <div class="cat">${cat}</div>
          </div>
        </div>
      </a>
    `;
  }).join("");

  append
    ? listEl.insertAdjacentHTML("beforeend", html)
    : (listEl.innerHTML = html);
}



async function load(reset = false) {
  if (reset) {
    listEl.innerHTML = "";
    nextPage = 0;
  }

  if (isLoading || nextPage === null) return;
  isLoading = true;

  const res = await fetch(buildURL(nextPage));
  const data = await res.json();

  render(data.data, !reset);
  nextPage = data.nextPage;
  isLoading = false;
}



new IntersectionObserver(entries => {
  if (entries[0].isIntersecting) load();
}).observe(sentinel);


async function loadCategories() {
  const res = await fetch("/api/categories");
  const data = await res.json();

  categoryList.innerHTML = data.data.map(c => `
    <button class="category-item" data-c="${c}">${c}</button>
  `).join("");

  categoryList.onclick = e => {
    if (!e.target.dataset.c) return;
    currentCategory = e.target.dataset.c;
    categoryText.textContent = currentCategory;
    categoryPanel.classList.add("hidden");
  };
}

categoryBtn.onclick = e => {
  e.stopPropagation();
  categoryPanel.classList.toggle("hidden");
};
document.onclick = () => categoryPanel.classList.add("hidden");


searchBtn.onclick = () => {
  currentKeyword = keywordInput.value.trim();
  load(true);
};


async function loadMRT() {
  const res = await fetch("/api/mrts");
  const data = await res.json();

  mrtList.innerHTML = data.data.map(m => `
    <button class="mrt-item" data-m="${m}">${m}</button>
  `).join("");

  mrtList.onclick = e => {
    if (!e.target.dataset.m) return;
    keywordInput.value = e.target.dataset.m;
    currentKeyword = e.target.dataset.m;
    load(true);
  };
}

mrtLeft.onclick = () => mrtScroll.scrollBy({ left: -300, behavior: "smooth" });
mrtRight.onclick = () => mrtScroll.scrollBy({ left: 300, behavior: "smooth" });



window.onload = async () => {
  await loadCategories();
  await loadMRT();
  await load(true);
};
