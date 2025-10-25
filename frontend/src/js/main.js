// ---------- Login ----------
const userInput = document.getElementById('userInput');
const passInput = document.getElementById('passInput');
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loginSection = document.getElementById('login');
const cardsSection = document.getElementById('cards');
const finderSection = document.getElementById('finder');
const historySection = document.getElementById('history');

loginBtn.onclick = () => {
  const user = userInput.value.trim();
  const pass = passInput.value.trim();
  if (user === 'admin' && pass === 'admin') {
    localStorage.setItem('user', user);
    showApp();
  } else {
    alert('Usuario o contraseña incorrectos.\nPrueba: admin / admin');
  }
};

logoutBtn.onclick = () => {
  localStorage.removeItem('user');
  hideApp();
};

function showApp() {
  loginSection.style.display = 'none';
  logoutBtn.style.display = 'block';
  cardsSection.style.display = 'flex';
  finderSection.style.display = 'block';
  historySection.style.display = 'block';
  loadRandomCards();
  renderHistory();
}

function hideApp() {
  loginSection.style.display = 'flex';
  logoutBtn.style.display = 'none';
  cardsSection.style.display = 'none';
  finderSection.style.display = 'none';
  historySection.style.display = 'none';
}

// ---------- 3 tarjetas aleatorias (fijas) ----------
const RANDOM_TITLES = ['el nombre del viento', 'don quijote de la mancha', 'cien años de soledad'];

async function loadRandomCards() {
  cardsSection.innerHTML = '';
  for (const titulo of RANDOM_TITLES) {
    const card = await fetchBookCard(titulo);
    if (card) cardsSection.appendChild(card);
  }
}

async function fetchBookCard(title) {
  try {
    const res = await fetch(`/api/books?title=${encodeURIComponent(title)}`);
    if (!res.ok) return null;
    const book = await res.json();
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="card-inner">
        <img class="card-image" src="${book.image}" alt="Portada" />
        <div class="card-body">
          <div class="card-title">${book.title}</div>
          <div class="card-authors">${book.authors.join(', ')}</div>
          <div class="card-desc-short">${book.description_short}</div>
        </div>
      </div>
      <div class="card-desc-box">
        <details>
          <summary>Descripción completa</summary>
          <p>${book.description_long}</p>
        </details>
      </div>
    `;
    return div;
  } catch { return null; }
}

// ---------- Buscador individual ----------
const titleInput = document.getElementById('titleInput');
const searchBtn = document.getElementById('searchBtn');
const result = document.getElementById('result');
const historyList = document.getElementById('historyList');
let history = [];

searchBtn.onclick = buscarLibro;
titleInput.addEventListener('keyup', e => { if (e.key === 'Enter') buscarLibro(); });

async function buscarLibro() {
  const titulo = titleInput.value.trim();
  if (!titulo) return;
  result.innerHTML = '<p class="error">Buscando…</p>';
  result.style.display = 'block';
  try {
    const res = await fetch(`/api/books?title=${encodeURIComponent(titulo)}`);
    if (!res.ok) throw new Error('Libro no encontrado');
    const book = await res.json();
    history.unshift({ ...book, searchedAt: new Date().toLocaleString() });
    renderHistory();
    result.innerHTML = `
      <div class="card">
        <div class="card-inner">
          <img class="card-image" src="${book.image}" alt="Portada" />
          <div class="card-body">
            <div class="card-title">${book.title}</div>
            <div class="card-authors">${book.authors.join(', ')}</div>
            <div class="card-desc-short">${book.description_short}</div>
          </div>
        </div>
        <div class="card-desc-box">
          <details>
            <summary>Descripción completa</summary>
            <p>${book.description_long}</p>
          </details>
        </div>
      </div>
    `;
  } catch (err) {
    result.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

// ---------- Historial temporal ----------
document.getElementById('clearBtn').onclick = () => { history = []; renderHistory(); };
function renderHistory() {
  historyList.innerHTML = history.length
    ? history.map((h, i) => `
        <div class="hist-card">
          <strong>${i + 1}.</strong> ${h.title} – ${h.authors.join(', ')}<br>
          <small>${h.searchedAt}</small>
        </div>
      `).join('')
    : '<p>Sin búsquedas aún</p>';
}

// ---------- Auto-login ----------
window.onload = () => {
  if (localStorage.getItem('user') === 'admin') {
    showApp();
  }
};