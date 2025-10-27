// ---------- Login ----------
const userInput = document.getElementById('userInput');
const passInput = document.getElementById('passInput');
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loginSection = document.getElementById('login');
const cardsSection = document.getElementById('cards');
const finderSection = document.getElementById('finder');
const historySection = document.getElementById('history');

let currentUserId = null;   // user_id real devuelto por el backend

loginBtn.onclick = async () => {
  const user = userInput.value.trim();
  const pass = passInput.value.trim();
  if (!user || !pass) return alert('Completa ambos campos');

  try {
    const res = await fetch(`/api/login?username=${encodeURIComponent(user)}&password=${encodeURIComponent(pass)}`, {
  method: 'POST'});
    if (!res.ok) throw new Error('Credenciales incorrectas');
    const data = await res.json();
    currentUserId = data.user_id;          // save real id
    localStorage.setItem('userId', currentUserId);
    showApp();
  } catch (e) {
    alert(e.message);
  }
};

logoutBtn.onclick = () => {
  localStorage.removeItem('userId');
  currentUserId = null;
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

// ---------- 3 tarjetas aleatorias ----------
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
    return mkCard(book);
  } catch { return null; }
}

function mkCard(book) {
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
}

// ---------- Buscador individual ----------
const titleInput = document.getElementById('titleInput');
const searchBtn = document.getElementById('searchBtn');
const result = document.getElementById('result');
const historyList = document.getElementById('historyList');

searchBtn.onclick = buscarLibro;
titleInput.addEventListener('keyup', e => { if (e.key === 'Enter') buscarLibro(); });

async function buscarLibro() {
  const titulo = titleInput.value.trim();
  if (!titulo) return;
  if (!currentUserId) return alert('Inicia sesión primero');
  result.innerHTML = '<p class="error">Buscando…</p>';
  result.style.display = 'block';
  try {
    // 1. traer libro
    const bookRes = await fetch(`/api/books?title=${encodeURIComponent(titulo)}`);
    if (!bookRes.ok) throw new Error('Libro no encontrado');
    const book = await bookRes.json();
    // 2. guardar búsqueda en BD
    await fetch(`/api/search?title=${encodeURIComponent(titulo)}&user_id=${currentUserId}`, { method: 'POST' });
    // 3. mostrar
    result.innerHTML = '';
    result.appendChild(mkCard(book));
    // 4. refrescar historial
    renderHistory();
  } catch (e) {
    result.innerHTML = `<p class="error">${e.message}</p>`;
  }
}

// ---------- Historial ----------
document.getElementById('clearBtn').onclick = async () => {
  if (!currentUserId) return;
  await fetch(`/api/history?user_id=${currentUserId}`, { method: 'DELETE' });
  renderHistory();
};

async function renderHistory() {
  if (!currentUserId) return;
  try {
    const res = await fetch(`/api/history?user_id=${currentUserId}`);
    const rows = await res.json();
    historyList.innerHTML = rows.length
      ? rows.map((h, i) => `
          <div class="hist-card">
            <strong>${i + 1}.</strong> ${h.book.title} – ${h.book.authors}<br>
            <small>${h.searched_at}</small>
          </div>
        `).join('')
      : '<p>Sin búsquedas aún</p>';
  } catch {
    historyList.innerHTML = '<p>Error al cargar historial</p>';
  }
}

// ---------- Auto-login ----------
window.onload = () => {
  const saved = localStorage.getItem('userId');
  if (saved) {
    currentUserId = saved;
    showApp();
  }
};