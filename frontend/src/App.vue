<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import logoUrl from './assets/img/logo.PNG';
import bannerUrl from './assets/img/banner.JPG';
import iconUrl from './assets/img/icon.png';

// Constants
const API_BASE_URL = '/api';

const CATEGORIES_AND_TYPES = {
  "infraestrutura": ["buracos em ruas", "problemas de infraestrutura"],
  "iluminação": ["iluminação pública quebrada"],
  "limpeza urbana": ["lixo acumulado", "descarte irregular de lixo"],
  "trânsito": ["sinalização danificada"],
  "saneamento": ["vazamentos"],
  "segurança pública": ["assaltos", "furtos", "vandalismo", "riscos à segurança pública"],
  "meio ambiente": ["poluição", "problemas ambientais"],
  "saúde urbana": ["focos de dengue"],
  "proteção animal": ["animais abandonados"],
  "emergências urbanas": ["situações de risco urbano"]
};

const PHOTO_TEMPLATES = {
  "infraestrutura": "https://images.unsplash.com/photo-1515162305285-0293e4767cc2?w=500&auto=format&fit=crop",
  "iluminação": "https://images.unsplash.com/photo-1509024644558-2f56ce76c490?w=500&auto=format&fit=crop",
  "limpeza urbana": "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=500&auto=format&fit=crop",
  "trânsito": "https://images.unsplash.com/photo-1518005020951-eccb494ad742?w=500&auto=format&fit=crop",
  "saneamento": "https://images.unsplash.com/photo-1542044896530-05d85be9b11a?w=500&auto=format&fit=crop",
  "segurança pública": "https://images.unsplash.com/photo-1508432296123-c4ec3e17529f?w=500&auto=format&fit=crop",
  "meio ambiente": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=500&auto=format&fit=crop",
  "saúde urbana": "https://images.unsplash.com/photo-1576086213369-97a306dca665?w=500&auto=format&fit=crop",
  "proteção animal": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=500&auto=format&fit=crop",
  "emergências urbanas": "https://images.unsplash.com/photo-1504151932400-72d425550d2e?w=500&auto=format&fit=crop"
};

const CATEGORY_NAMES = {
  "infraestrutura": "🚧 Infraestrutura",
  "iluminação": "💡 Iluminação",
  "limpeza urbana": "🧹 Limpeza Urbana",
  "trânsito": "🚦 Trânsito",
  "saneamento": "🚰 Saneamento",
  "segurança pública": "🛡️ Segurança Pública",
  "meio ambiente": "🌱 Meio Ambiente",
  "saúde urbana": "🦟 Saúde Urbana",
  "proteção animal": "🐾 Proteção Animal",
  "emergências urbanas": "⚠️ Emergências Urbanas"
};

const TYPE_NAMES = {
  "buracos em ruas": "🕳️ Buracos em Ruas",
  "iluminação pública quebrada": "💡 Iluminação Pública Quebrada",
  "lixo acumulado": "🗑️ Lixo Acumulado",
  "vazamentos": "💧 Vazamentos",
  "sinalização danificada": "🛑 Sinalização Danificada",
  "problemas de infraestrutura": "🏗️ Problemas de Infraestrutura",
  "assaltos": "🔫 Assaltos",
  "furtos": "💸 Furtos",
  "vandalismo": "🔨 Vandalismo",
  "animais abandonados": "🐕 Animais Abandonados",
  "focos de dengue": "🦟 Focos de Dengue",
  "descarte irregular de lixo": "🚯 Descarte Irregular de Lixo",
  "poluição": "🏭 Poluição",
  "riscos à segurança pública": "🚨 Riscos à Segurança Pública",
  "problemas ambientais": "🌳 Problemas Ambientais",
  "situações de risco urbano": "⚠️ Situações de Risco Urbano"
};

function sanitizeCategoryClass(category) {
  if (!category) return 'outros';
  return category
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, '-');
}

// --- AUTHENTICATION STATE ---
const isAuthenticated = ref(false);
const authMode = ref('login'); // 'login', 'register', 'forgot', 'reset'
const userEmail = ref('');
const userRole = ref('');
const userId = ref(null);
const authToken = ref('');

// Auth inputs
const inputEmail = ref('');
const inputPassword = ref('');
const inputConfirmPassword = ref('');
const resetToken = ref('');
const resetPasswordVal = ref('');
const authMessage = ref('');
const authError = ref('');

// --- APP STATE ---
const occurrences = ref([]);
const activeTab = ref('list');
const searchQuery = ref('');
const categoryFilter = ref('');
const statusFilter = ref('');

// Form State
const formLat = ref(null);
const formLng = ref(null);
const formCategory = ref('');
const formTitle = ref('');
const formDescription = ref('');
const formPhoto = ref('');
const formType = ref('');

// Map State
let map = null;
let markers = {};
let tempMarker = null;

// Error & Status Message State
const errorMessage = ref('');

// --- ADMIN STATE ---
const toggles = ref({
  allow_personal_occurrences: true,
  allow_mock_photos: true,
  read_only_mode: false
});
const adminUsersList = ref([]);

// Computed Stats
const totalCount = computed(() => occurrences.value.length);
const pendingCount = computed(() => occurrences.value.filter(o => o.status === 'pendente').length);
const progressCount = computed(() => occurrences.value.filter(o => o.status === 'progresso').length);
const resolvedCount = computed(() => occurrences.value.filter(o => o.status === 'resolvido').length);

const availableTypes = computed(() => {
  if (!formCategory.value) return [];
  return CATEGORIES_AND_TYPES[formCategory.value] || [];
});

function onCategoryChange() {
  formType.value = '';
}

// Computed Filtered List
const filteredOccurrences = computed(() => {
  const query = searchQuery.value.toLowerCase();
  return occurrences.value.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(query) || 
                          item.description.toLowerCase().includes(query);
    const matchesCategory = !categoryFilter.value || item.category === categoryFilter.value;
    const matchesStatus = !statusFilter.value || item.status === statusFilter.value;
    
    // Admin Toggle filters out personal occurrences if deactivated
    const matchesToggle = toggles.value.allow_personal_occurrences || item.category !== 'segurança pública';

    return matchesSearch && matchesCategory && matchesStatus && matchesToggle;
  });
});

// Watch filters to update map markers
watch([filteredOccurrences], () => {
  updateMapMarkers();
});

// Lifecycle
onMounted(() => {
  checkLocalAuth();
});

// Check if credentials exist in localStorage
function checkLocalAuth() {
  const token = localStorage.getItem('riou_token');
  const email = localStorage.getItem('riou_email');
  const role = localStorage.getItem('riou_role');
  const id = localStorage.getItem('riou_id');
  
  if (token && email && role && id) {
    authToken.value = token;
    userEmail.value = email;
    userRole.value = role;
    userId.value = parseInt(id, 10);
    isAuthenticated.value = true;
    
    // Init app
    nextTick(() => {
      initMap();
      fetchOccurrences();
      if (role === 'admin') {
        fetchAdminToggles();
      }
    });
  }
}

// Expose popup functions
window.updateOccurrenceStatus = (id, newStatus) => {
  updateStatus(id, newStatus);
};
window.deleteOccurrence = (id) => {
  removeOccurrence(id);
};

// API Request Wrapper with JWT Authentication
async function apiFetch(path, options = {}) {
  const headers = { ...options.headers };
  if (authToken.value) {
    headers['Authorization'] = `Bearer ${authToken.value}`;
  }
  
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });
  
  if (res.status === 401) {
    // Session expired
    handleLogout();
    throw new Error('Sessão expirada. Faça login novamente.');
  }
  
  return res;
}

// --- AUTHENTICATION METHODS ---

async function handleLogin() {
  authError.value = '';
  authMessage.value = '';
  
  const formData = new URLSearchParams();
  formData.append('username', inputEmail.value);
  formData.append('password', inputPassword.value);

  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'E-mail ou senha incorretos.');
    }

    const data = await res.json();
    
    // Save locally
    localStorage.setItem('riou_token', data.access_token);
    localStorage.setItem('riou_email', data.email);
    localStorage.setItem('riou_role', data.role);
    localStorage.setItem('riou_id', data.id);

    authToken.value = data.access_token;
    userEmail.value = data.email;
    userRole.value = data.role;
    userId.value = data.id;
    isAuthenticated.value = true;

    // Reset login inputs
    inputEmail.value = '';
    inputPassword.value = '';

    // Initialize UI
    nextTick(() => {
      initMap();
      fetchOccurrences();
      if (data.role === 'admin') {
        fetchAdminToggles();
      }
    });

  } catch (err) {
    authError.value = err.message;
  }
}

async function handleRegister() {
  authError.value = '';
  authMessage.value = '';

  if (inputPassword.value !== inputConfirmPassword.value) {
    authError.value = 'As senhas não coincidem.';
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: inputEmail.value,
        password: inputPassword.value
      })
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao registrar conta.');
    }

    authMessage.value = 'Conta cadastrada com sucesso! Faça seu login.';
    authMode.value = 'login';
    inputPassword.value = '';
    inputConfirmPassword.value = '';

  } catch (err) {
    authError.value = err.message;
  }
}

async function handleForgotPassword() {
  authError.value = '';
  authMessage.value = '';

  try {
    const res = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: inputEmail.value })
    });

    const data = await res.json();
    
    authMessage.value = data.message;
    
    // For development ease, capture the debug token from response if present
    if (data.debug_token) {
      resetToken.value = data.debug_token;
    }
    
    authMode.value = 'reset';
  } catch (err) {
    authError.value = 'Erro ao solicitar recuperação.';
  }
}

async function handleResetPassword() {
  authError.value = '';
  authMessage.value = '';

  try {
    const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: inputEmail.value,
        token: resetToken.value,
        new_password: resetPasswordVal.value
      })
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Token ou e-mail inválidos.');
    }

    authMessage.value = 'Senha redefinida com sucesso! Pode entrar.';
    authMode.value = 'login';
    resetToken.value = '';
    resetPasswordVal.value = '';
    inputEmail.value = '';
  } catch (err) {
    authError.value = err.message;
  }
}

function handleLogout() {
  localStorage.removeItem('riou_token');
  localStorage.removeItem('riou_email');
  localStorage.removeItem('riou_role');
  localStorage.removeItem('riou_id');
  
  authToken.value = '';
  userEmail.value = '';
  userRole.value = '';
  userId.value = null;
  isAuthenticated.value = false;
  
  // Clean map
  if (map) {
    map.remove();
    map = null;
  }
  markers = {};
  tempMarker = null;
  occurrences.value = [];
}

// --- DATA ACCESS METHODS ---

async function fetchOccurrences() {
  try {
    errorMessage.value = '';
    const res = await apiFetch('/ocorrencias');
    occurrences.value = await res.json();
    updateMapMarkers();
  } catch (err) {
    errorMessage.value = err.message || 'Erro ao carregar ocorrências.';
    console.error(err);
  }
}

async function createOccurrence() {
  if (!formLat.value || !formLng.value) {
    alert("Por favor, clique no mapa para selecionar as coordenadas.");
    return;
  }

  if (formCategory.value === 'segurança pública' && !toggles.value.allow_personal_occurrences) {
    alert("O cadastro de ocorrências de segurança pública está desabilitado pelo administrador.");
    return;
  }

  const payload = {
    title: formTitle.value,
    category: formCategory.value,
    description: formDescription.value,
    lat: parseFloat(formLat.value),
    lng: parseFloat(formLng.value),
    photo: formPhoto.value || null,
    type: formType.value
  };

  try {
    const res = await apiFetch('/ocorrencias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao criar ocorrência.');
    }
    const newRecord = await res.json();
    
    occurrences.value.unshift(newRecord);
    
    resetForm();
    switchTab('list');
    
    setTimeout(() => {
      focusOccurrence(newRecord.id);
    }, 400);

  } catch (err) {
    alert(err.message || "Erro ao salvar o registro no banco.");
    console.error(err);
  }
}

async function updateStatus(id, newStatus) {
  try {
    const res = await apiFetch(`/ocorrencias/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao atualizar status.');
    }
    const updatedRecord = await res.json();

    const index = occurrences.value.findIndex(o => o.id === id);
    if (index !== -1) {
      occurrences.value[index] = updatedRecord;
    }

    const marker = markers[id];
    if (marker) {
      marker.setPopupContent(createPopupContent(updatedRecord));
      
      const node = marker.getElement();
      if (node) {
        const innerNode = node.querySelector('.custom-marker-node');
        if (innerNode) {
          innerNode.style.transform = 'scale(1.3)';
          setTimeout(() => {
            innerNode.style.transform = 'scale(1)';
          }, 300);
        }
      }
    }
  } catch (err) {
    alert(err.message);
    // Reload markers to reset selector
    fetchOccurrences();
  }
}

async function removeOccurrence(id) {
  if (!confirm("Tem certeza que deseja excluir esta ocorrência definitivamente?")) return;

  try {
    const res = await apiFetch(`/ocorrencias/${id}`, {
      method: 'DELETE'
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao deletar.');
    }

    occurrences.value = occurrences.value.filter(o => o.id !== id);
    
    if (markers[id]) {
      map.removeLayer(markers[id]);
      delete markers[id];
    }
  } catch (err) {
    alert(err.message);
  }
}

// --- ADMIN PANEL METHODS ---

async function fetchAdminToggles() {
  try {
    const res = await apiFetch('/admin/toggles');
    const togglesList = await res.json();
    togglesList.forEach(t => {
      if (t.key in toggles.value) {
        toggles.value[t.key] = t.value;
      }
    });
  } catch (err) {
    console.error("Erro ao carregar toggles", err);
  }
}

async function saveAdminToggle(key, val) {
  try {
    await apiFetch('/admin/toggles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value: val })
    });
    // Trigger marker refresh if personal occurrences toggled
    if (key === 'allow_personal_occurrences') {
      fetchOccurrences();
    }
  } catch (err) {
    console.error("Erro ao salvar toggle admin", err);
  }
}

async function executeBatchResolve() {
  if (!confirm("Deseja marcar todas as ocorrências pendentes e em curso como Resolvidas?")) return;
  try {
    const res = await apiFetch('/admin/batch-resolve', { method: 'POST' });
    const data = await res.json();
    alert(data.message);
    fetchOccurrences();
  } catch (err) {
    alert("Erro ao executar ação em lote.");
  }
}

async function fetchUsersList() {
  try {
    const res = await apiFetch('/admin/users');
    adminUsersList.value = await res.json();
  } catch (err) {
    console.error("Erro ao listar usuários", err);
  }
}

async function banUser(userIdVal, durationMinutes) {
  if (durationMinutes <= 0) return;
  try {
    const res = await apiFetch(`/admin/users/${userIdVal}/ban`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duration_minutes: durationMinutes })
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao banir usuário.');
    }
    alert("Usuário banido com sucesso!");
    fetchUsersList();
  } catch (err) {
    alert(err.message);
  }
}

async function unbanUser(userIdVal) {
  if (!confirm("Deseja desbanir este usuário?")) return;
  try {
    const res = await apiFetch(`/admin/users/${userIdVal}/ban`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duration_minutes: 0 })
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao desbanir usuário.');
    }
    alert("Usuário desbanido com sucesso!");
    fetchUsersList();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteUserAccount(userIdVal) {
  if (!confirm("Tem certeza que deseja excluir esta conta definitivamente? Todas as ocorrências deste usuário ficarão sem criador associado.")) return;
  try {
    const res = await apiFetch(`/admin/users/${userIdVal}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erro ao excluir conta.');
    }
    alert("Conta excluída com sucesso!");
    fetchUsersList();
  } catch (err) {
    alert(err.message);
  }
}

// --- MAP & MARKERS ---

function initMap() {
  if (map) return;
  const centralLat = -7.136;
  const centralLng = -34.845;
  
  map = window.L.map('map', {
    zoomControl: false
  }).setView([centralLat, centralLng], 15);

  window.L.control.zoom({
    position: 'topright'
  }).addTo(map);

  window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
  }).addTo(map);

  map.on('click', (e) => {
    const { lat, lng } = e.latlng;
    
    if (tempMarker) {
      map.removeLayer(tempMarker);
    }
    
    const tempIcon = window.L.divIcon({
      html: `<div style="
        display: flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: rgba(128, 29, 42, 0.2);
        border: 2.5px dashed #801d2a;
        font-size: 16px;
      ">🔻</div>`,
      className: 'temp-marker-icon',
      iconSize: [38, 38],
      iconAnchor: [19, 19]
    });
    
    tempMarker = window.L.marker([lat, lng], { icon: tempIcon }).addTo(map);
    
    formLat.value = lat.toFixed(6);
    formLng.value = lng.toFixed(6);
    
    switchTab('form');
  });
}

function updateMapMarkers() {
  if (!map) return;

  Object.values(markers).forEach(m => map.removeLayer(m));
  markers = {};

  filteredOccurrences.value.forEach(item => {
    const color = getCategoryColor(item.category);
    const emoji = getCategoryEmoji(item.category);

    const customIcon = window.L.divIcon({
      html: `<div style="
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(15, 23, 42, 0.85);
        border: 2.5px solid ${color};
        box-shadow: 0 0 15px ${color};
        font-size: 18px;
        cursor: pointer;
        transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      " class="custom-marker-node">
        ${emoji}
      </div>`,
      className: `custom-marker-${sanitizeCategoryClass(item.category)}`,
      iconSize: [36, 36],
      iconAnchor: [18, 18]
    });

    const marker = window.L.marker([item.lat, item.lng], { icon: customIcon }).addTo(map);
    marker.bindPopup(createPopupContent(item));
    
    marker.on('click', () => {
      highlightListItem(item.id);
    });

    markers[item.id] = marker;
  });
}

function createPopupContent(item) {
  const dateFormatted = new Date(item.date).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
  const imgHtml = item.photo ? `<img src="${item.photo}" class="map-popup-img" alt="Ocorrência" onerror="this.style.display='none'">` : '';
  
  const isSecurity = item.category === 'segurança pública';
  const badgeStyle = isSecurity 
    ? 'background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4);' 
    : 'background: rgba(255,255,255,0.08); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.15);';
  
  const typeText = TYPE_NAMES[item.type] ? TYPE_NAMES[item.type].split(' ').slice(1).join(' ') : item.type;
  const typeBadge = `<span style="${badgeStyle} font-size:9px; padding: 2px 6px; border-radius:4px; margin-left:6px; font-weight:700; text-transform:uppercase;">${typeText}</span>`;
  
  const showDelete = userRole.value === 'admin' || (item.user_id === userId.value);
  const deleteBtn = showDelete ? `
    <button class="btn-delete" onclick="window.deleteOccurrence(${item.id})">
      Excluir
    </button>
  ` : '';
  
  const showStatusSelect = userRole.value === 'admin';
  const statusHtml = showStatusSelect ? `
    <select onchange="window.updateOccurrenceStatus(${item.id}, this.value)">
      <option value="pendente" ${item.status === 'pendente' ? 'selected' : ''}>Pendente</option>
      <option value="progresso" ${item.status === 'progresso' ? 'selected' : ''}>Em Curso</option>
      <option value="resolvido" ${item.status === 'resolvido' ? 'selected' : ''}>Resolvido</option>
    </select>
  ` : `
    <span style="font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase; padding: 4px 8px; background:rgba(255,255,255,0.05); border-radius:4px;">
      ${item.status === 'pendente' ? 'Pendente' : item.status === 'progresso' ? 'Em Curso' : 'Resolvido'}
    </span>
  `;

  return `
    <div class="map-popup-card">
      <div class="map-popup-header">
        <span class="map-popup-title">${item.title} ${typeBadge}</span>
      </div>
      ${imgHtml}
      <div class="map-popup-desc">
        <strong style="color: #cbd5e1;">Categoria:</strong> ${CATEGORY_NAMES[item.category] || item.category}<br>
        <strong style="color: #cbd5e1;">Reportado em:</strong> ${dateFormatted}<br>
        <p style="margin-top: 4px; color: #94a3b8;">${item.description}</p>
      </div>
      <div class="map-popup-actions">
        ${statusHtml}
        ${deleteBtn}
      </div>
    </div>
  `;
}

// Helpers
function getCategoryColor(category) {
  const colors = {
    "infraestrutura": "#f97316",
    "iluminação": "#eab308",
    "limpeza urbana": "#a855f7",
    "trânsito": "#3b82f6",
    "saneamento": "#06b6d4",
    "segurança pública": "#ef4444",
    "meio ambiente": "#22c55e",
    "saúde urbana": "#14b8a6",
    "proteção animal": "#ec4899",
    "emergências urbanas": "#f43f5e"
  };
  return colors[category] || '#64748b';
}

function getCategoryEmoji(category) {
  const emojis = {
    "infraestrutura": "🚧",
    "iluminação": "💡",
    "limpeza urbana": "🧹",
    "trânsito": "🚦",
    "saneamento": "🚰",
    "segurança pública": "🛡️",
    "meio ambiente": "🌱",
    "saúde urbana": "🦟",
    "proteção animal": "🐾",
    "emergências urbanas": "⚠️"
  };
  return emojis[category] || '📍';
}

function focusOccurrence(id) {
  const item = occurrences.value.find(o => o.id === id);
  if (!item) return;

  map.setView([item.lat, item.lng], 17, { animate: true, duration: 0.8 });
  const marker = markers[id];
  if (marker) {
    marker.openPopup();
  }
  highlightListItem(id);
}

function highlightListItem(id) {
  document.querySelectorAll('.occurrence-card').forEach(card => card.classList.remove('selected'));
  const card = document.getElementById(`card-${id}`);
  if (card) {
    card.classList.add('selected');
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function switchTab(tabName) {
  activeTab.value = tabName;
  if (tabName === 'list' && tempMarker) {
    map.removeLayer(tempMarker);
    tempMarker = null;
    resetForm();
  }
  if (tabName === 'admin') {
    fetchUsersList();
  }
}

function resetForm() {
  formLat.value = null;
  formLng.value = null;
  formCategory.value = '';
  formTitle.value = '';
  formDescription.value = '';
  formPhoto.value = '';
  formType.value = '';
}

function clearFilters() {
  searchQuery.value = '';
  categoryFilter.value = '';
  statusFilter.value = '';
}

function generateMockPhoto() {
  if (!formCategory.value) {
    alert("Por favor, selecione uma categoria antes de gerar a foto.");
    return;
  }
  const randomSeed = Math.floor(Math.random() * 100);
  formPhoto.value = `${PHOTO_TEMPLATES[formCategory.value]}&sig=${randomSeed}`;
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit'
  });
}
</script>

<template>
  <!-- 1. LOGIN / AUTHENTICATION LAYER -->
  <div v-if="!isAuthenticated" class="auth-layer">
    <div class="auth-left">
      <div class="auth-box glass-card">
        <div class="auth-logo">
          <img :src="logoUrl" alt="RIOU" class="auth-logo-img" />
        </div>
        <p class="auth-subtitle">Registro Inteligente de Ocorrências Urbanas</p>

        <!-- Messages alerts -->
        <div v-if="authMessage" class="auth-alert success">{{ authMessage }}</div>
        <div v-if="authError" class="auth-alert error">{{ authError }}</div>

        <!-- Mode 1: Login -->
        <form v-if="authMode === 'login'" @submit.prevent="handleLogin">
          <div class="form-group">
            <label>E-mail</label>
            <input type="email" required v-model="inputEmail" placeholder="exemplo@gmail.com">
          </div>
          <div class="form-group">
            <label>Senha</label>
            <input type="password" required v-model="inputPassword" placeholder="******">
          </div>
          <button type="submit" class="btn btn-primary btn-block">Entrar</button>
          <div class="auth-links">
            <a href="#" @click.prevent="authMode = 'register'">Criar Conta</a>
            <a href="#" @click.prevent="authMode = 'forgot'">Esqueci a Senha</a>
          </div>
        </form>

        <!-- Mode 2: Register -->
        <form v-if="authMode === 'register'" @submit.prevent="handleRegister">
          <div class="form-group">
            <label>E-mail</label>
            <input type="email" required v-model="inputEmail" placeholder="exemplo@gmail.com">
          </div>
          <div class="form-group">
            <label>Senha</label>
            <input type="password" required v-model="inputPassword" placeholder="Mínimo 6 caracteres">
          </div>
          <div class="form-group">
            <label>Confirmar Senha</label>
            <input type="password" required v-model="inputConfirmPassword" placeholder="Repita a senha">
          </div>
          <button type="submit" class="btn btn-primary btn-block">Cadastrar</button>
          <div class="auth-links">
            <a href="#" @click.prevent="authMode = 'login'">Já tenho uma conta (Login)</a>
          </div>
        </form>

        <!-- Mode 3: Forgot Password -->
        <form v-if="authMode === 'forgot'" @submit.prevent="handleForgotPassword">
          <div class="form-group">
            <label>E-mail cadastrado</label>
            <input type="email" required v-model="inputEmail" placeholder="exemplo@gmail.com">
          </div>
          <button type="submit" class="btn btn-primary btn-block">Solicitar Código</button>
          <div class="auth-links">
            <a href="#" @click.prevent="authMode = 'login'">Voltar ao Login</a>
          </div>
        </form>

        <!-- Mode 4: Reset Password -->
        <form v-if="authMode === 'reset'" @submit.prevent="handleResetPassword">
          <div class="alert-info-box" style="margin-bottom:12px; font-size:11px;">
            <span>Copie o token gerado nos logs do container do Backend para concluir a redefinição.</span>
          </div>
          <div class="form-group">
            <label>Token de Recuperação</label>
            <input type="text" required v-model="resetToken" placeholder="reset-xxxxxx">
          </div>
          <div class="form-group">
            <label>Nova Senha</label>
            <input type="password" required v-model="resetPasswordVal" placeholder="Nova senha (mínimo 6)">
          </div>
          <button type="submit" class="btn btn-primary btn-block">Salvar Nova Senha</button>
          <div class="auth-links">
            <a href="#" @click.prevent="authMode = 'login'">Cancelar e Voltar</a>
          </div>
        </form>
      </div>
    </div>
    <div class="auth-right"></div>
  </div>

  <!-- 2. CORE APPLICATION (authenticated) -->
  <div v-else class="app-container">
    
    <!-- Sidebar / Controle -->
    <aside class="sidebar">
      <header class="app-header">
        <div class="logo">
          <img :src="logoUrl" alt="RIOU" class="logo-img" />
        </div>
        <div class="user-meta-row">
          <span class="user-email-tag" :title="userEmail">{{ userEmail }}</span>
          <button class="btn-logout" @click="handleLogout" title="Sair">Sair</button>
        </div>
      </header>

      <!-- Connection Error Alert -->
      <div v-if="errorMessage" class="alert-info-box" style="margin: 16px 24px 0; background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #f87171;">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <span>{{ errorMessage }}</span>
      </div>

      <!-- System Stats -->
      <section v-if="userRole === 'admin'" class="stats-grid">
        <div class="stat-card total">
          <span class="stat-value">{{ totalCount }}</span>
          <span class="stat-label">Total</span>
        </div>
        <div class="stat-card pending">
          <span class="stat-value">{{ pendingCount }}</span>
          <span class="stat-label">Pendentes</span>
        </div>
        <div class="stat-card progress">
          <span class="stat-value">{{ progressCount }}</span>
          <span class="stat-label">Em Curso</span>
        </div>
        <div class="stat-card resolved">
          <span class="stat-value">{{ resolvedCount }}</span>
          <span class="stat-label">Resolvidas</span>
        </div>
      </section>

      <!-- Tabs Nav -->
      <div class="tabs-nav">
        <button class="tab-btn" :class="{ active: activeTab === 'list' }" @click="switchTab('list')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
          Ocorrências
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'form' }" @click="switchTab('form')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
          Novo Reporte
        </button>
        <!-- ADMIN TAB: Only visible if role is admin -->
        <button v-if="userRole === 'admin'" class="tab-btn" :class="{ active: activeTab === 'admin' }" @click="switchTab('admin')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          Admin
        </button>
      </div>

      <!-- Tab Content Panel -->
      <div class="panel-content">
        
        <!-- Tab 1: List -->
        <div v-show="activeTab === 'list'" class="tab-panel active">
          <div class="search-filter-box">
            <div class="search-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" v-model="searchQuery" placeholder="Buscar ocorrência...">
            </div>
            
            <div class="filters-row">
              <select v-model="categoryFilter" class="filter-select">
                <option value="">Todas as Categorias</option>
                <option v-for="(name, cat) in CATEGORY_NAMES" :key="cat" :value="cat">
                  {{ name }}
                </option>
              </select>
              
              <select v-model="statusFilter" class="filter-select">
                <option value="">Todos os Status</option>
                <option value="pendente">Pendente</option>
                <option value="progresso">Em Curso</option>
                <option value="resolvido">Resolvido</option>
              </select>
            </div>
          </div>

          <div class="occurrences-list">
            <div v-if="filteredOccurrences.length === 0" class="empty-state">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="empty-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <p>Nenhuma ocorrência encontrada.</p>
              <button class="btn btn-secondary btn-small" @click="clearFilters">Limpar Filtros</button>
            </div>
            
            <div 
              v-for="item in filteredOccurrences" 
              :key="item.id" 
              class="occurrence-card"
              :class="[`cat-${sanitizeCategoryClass(item.category)}`, `card-${item.id}`, { 'type-pessoal': item.category === 'segurança pública' }]"
              :id="`card-${item.id}`"
              @click="focusOccurrence(item.id)"
            >
              <div class="card-header">
                <span class="card-title">
                  {{ item.title }} 
                  <span v-if="item.category === 'segurança pública'" class="admin-badge text-pessoal">Segurança</span>
                </span>
                <span class="badge-status" :class="item.status">
                  {{ item.status === 'pendente' ? 'Pendente' : item.status === 'progresso' ? 'Em Curso' : 'Resolvido' }}
                </span>
              </div>
              <p class="card-desc">{{ item.description }}</p>
              <div class="card-meta">
                <span class="card-category-tag">
                  {{ getCategoryEmoji(item.category) }} 
                  {{ CATEGORY_NAMES[item.category] ? CATEGORY_NAMES[item.category].split(' ').slice(1).join(' ') : item.category }}
                  <span class="card-type-tag" style="margin-left: 6px; padding-left: 6px; border-left: 1px solid rgba(255,255,255,0.15);">
                    {{ TYPE_NAMES[item.type] ? TYPE_NAMES[item.type].split(' ').slice(1).join(' ') : item.type }}
                  </span>
                </span>
                <span class="card-date">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  {{ formatDate(item.date) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: Form -->
        <div v-show="activeTab === 'form'" class="tab-panel active">
          <form class="report-form" @submit.prevent="createOccurrence">
            <!-- Read Only mode blocker message -->
            <div v-if="toggles.read_only_mode && userRole !== 'admin'" class="alert-info-box" style="background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #f87171;">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <span>A plataforma está bloqueada para escrita. Somente leitura ativa.</span>
            </div>
            
            <div v-else class="alert-info-box">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>Clique no mapa no local exato da ocorrência para preencher as coordenadas.</span>
            </div>

            <!-- Position Coordinates -->
            <div class="form-group row">
              <div class="col">
                <label>Latitude <span class="required">*</span></label>
                <input type="number" step="any" readonly required v-model="formLat" placeholder="Clique no mapa">
              </div>
              <div class="col">
                <label>Longitude <span class="required">*</span></label>
                <input type="number" step="any" readonly required v-model="formLng" placeholder="Clique no mapa">
              </div>
            </div>

            <div class="form-group">
              <label>Categoria <span class="required">*</span></label>
              <select v-model="formCategory" @change="onCategoryChange" required>
                <option value="" disabled>Selecione uma categoria</option>
                <option v-for="(name, cat) in CATEGORY_NAMES" :key="cat" :value="cat" :disabled="cat === 'segurança pública' && !toggles.allow_personal_occurrences">
                  {{ name }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>Tipo de Ocorrência <span class="required">*</span></label>
              <select v-model="formType" :disabled="!formCategory" required>
                <option value="" disabled>{{ formCategory ? 'Selecione o tipo de ocorrência' : 'Selecione uma categoria primeiro' }}</option>
                <option v-for="t in availableTypes" :key="t" :value="t">
                  {{ TYPE_NAMES[t] || t }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>Título / Resumo Curto <span class="required">*</span></label>
              <input type="text" required v-model="formTitle" placeholder="Ex: Assalto armado / Buraco profundo">
            </div>

            <div class="form-group">
              <label>Descrição Detalhada <span class="required">*</span></label>
              <textarea rows="3" required v-model="formDescription" placeholder="Descreva os detalhes do problema para facilitar o suporte ou reparo..."></textarea>
            </div>

            <div class="form-group">
              <label>URL da Imagem / Foto (Opcional)</label>
              <div class="photo-input-wrapper">
                <input type="url" v-model="formPhoto" placeholder="https://exemplo.com/foto.jpg">
                <button v-if="toggles.allow_mock_photos" type="button" class="btn btn-secondary btn-small" @click="generateMockPhoto">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                  Gerar Mock
                </button>
              </div>
              <span class="input-tip">Adicione uma foto ou clique no botão para usar um mock automático da categoria.</span>
            </div>

            <div class="form-actions">
              <button type="button" class="btn btn-ghost" @click="switchTab('list')">Cancelar</button>
              <button v-if="!toggles.read_only_mode || userRole === 'admin'" type="submit" class="btn btn-primary">Registrar Ocorrência</button>
            </div>
          </form>
        </div>

        <!-- Tab 3: Admin Dashboard panel -->
        <div v-show="activeTab === 'admin'" class="tab-panel active">
          <div class="admin-section">
            <h3 class="admin-title">Feature Toggles (Controle do Sistema)</h3>
            
            <div class="toggle-card">
              <div class="toggle-info">
                <h4>Habilitar Ocorrências Pessoais</h4>
                <p>Permite ou bloqueia relatos pessoais e de segurança (como roubos) no mapa e formulário.</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="toggles.allow_personal_occurrences" @change="saveAdminToggle('allow_personal_occurrences', toggles.allow_personal_occurrences)">
                <span class="slider round"></span>
              </label>
            </div>

            <div class="toggle-card">
              <div class="toggle-info">
                <h4>Habilitar Gerador de Foto Mock</h4>
                <p>Mostra ou oculta o botão que ajuda desenvolvedores a preencherem fotos fictícias de forma rápida.</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="toggles.allow_mock_photos" @change="saveAdminToggle('allow_mock_photos', toggles.allow_mock_photos)">
                <span class="slider round"></span>
              </label>
            </div>

            <div class="toggle-card">
              <div class="toggle-info">
                <h4>Modo Somente Leitura</h4>
                <p>Bloqueia a inserção de novos relatos ou alteração de status por cidadãos comuns.</p>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="toggles.read_only_mode" @change="saveAdminToggle('read_only_mode', toggles.read_only_mode)">
                <span class="slider round"></span>
              </label>
            </div>
          </div>

          <div class="admin-section" style="margin-top: 24px;">
            <h3 class="admin-title">Ações Administrativas</h3>
            <button class="btn btn-secondary btn-block" @click="executeBatchResolve" style="border-color: var(--status-resolved-border); color: var(--status-resolved-color); background: rgba(16, 185, 129, 0.05);">
              Resolver Todas as Ocorrências Abertas (Batch Resolve)
            </button>
          </div>

          <div class="admin-section" style="margin-top: 28px;">
            <h3 class="admin-title">Usuários Cadastrados ({{ adminUsersList.length }})</h3>
            <div class="admin-users-list">
              <div v-for="u in adminUsersList" :key="u.id" class="admin-user-card">
                <div style="display:flex; flex-direction:column; flex: 1;">
                  <span class="admin-user-email">{{ u.email }}</span>
                  <div style="display: flex; gap: 8px; align-items: center; margin-top: 2px;">
                    <span class="admin-user-id">ID: #{{ u.id }}</span>
                    <span v-if="u.banned_until && new Date(u.banned_until) > new Date()" class="ban-tag">
                      Banido até {{ new Date(u.banned_until).toLocaleString('pt-BR') }}
                    </span>
                  </div>
                </div>
                <div class="admin-user-actions">
                  <span class="admin-badge" :class="u.role === 'admin' ? 'admin-pill' : 'user-pill'" style="margin-right: 8px;">
                    {{ u.role }}
                  </span>
                  <template v-if="u.role !== 'admin'">
                    <button v-if="u.banned_until && new Date(u.banned_until) > new Date()" class="btn-action unban" @click="unbanUser(u.id)">
                      Desbanir
                    </button>
                    <div v-else class="ban-select-wrapper">
                      <select class="ban-select" @change="e => { if(e.target.value) { banUser(u.id, parseInt(e.target.value)); e.target.value = ''; } }">
                        <option value="">Banir...</option>
                        <option value="5">5 min</option>
                        <option value="60">1 hora</option>
                        <option value="1440">1 dia</option>
                        <option value="10080">1 semana</option>
                      </select>
                    </div>
                    <button class="btn-action delete" @click="deleteUserAccount(u.id)">
                      Excluir
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
        
      </div>
      
      <footer class="sidebar-footer">
        <span>© 2026 RIOU. Todos os direitos reservados.</span>
      </footer>
    </aside>

    <!-- Área do Mapa -->
    <main class="map-wrapper">
      <div id="map"></div>
      
      <!-- Quick Floating Action -->
      <div class="map-overlay-info">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="pulse-icon"><polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7Z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7Z"/></svg>
        <span>Clique no mapa para registrar uma ocorrência</span>
      </div>
    </main>
    
  </div>
</template>

<style scoped>
/* Specific scoped adjustments for animations inside Vue */
.custom-marker-node {
  animation: markerEntry 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes markerEntry {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.admin-user-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ban-tag {
  font-size: 10px;
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.btn-action {
  font-family: var(--font-primary);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: var(--transition-smooth);
}
.btn-action.unban {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.btn-action.unban:hover {
  background: rgba(16, 185, 129, 0.3);
}
.btn-action.delete {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.btn-action.delete:hover {
  background: rgba(239, 68, 68, 0.3);
}
.ban-select-wrapper {
  position: relative;
}
.ban-select {
  padding: 4px 6px;
  font-size: 11px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
}
.ban-select:focus {
  border-color: var(--color-primary);
}
</style>
