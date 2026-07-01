import http from 'k6/http';
import { check, sleep, group } from 'k6';

// ─────────────────────────────────────────────────────────────────────────────
// Teste de carga e performance — k6
//
// IMPORTANTE: rode contra o SEU AMBIENTE LOCAL (suba o projeto com
// docker-compose antes). NÃO aponte para https://eqNN.dsc.rodrigor.com — o
// servidor e o PostgreSQL são compartilhados com as outras equipes.
// ─────────────────────────────────────────────────────────────────────────────

// URL base do seu ambiente local. Ajuste a porta se exposta de forma diferente.
const BASE = __ENV.BASE_URL || 'http://localhost:8120';

// Nº de usuários virtuais simultâneos. Sobrescreva pela linha de comando:
//   k6 run -e VUS=20 -e BASE_URL=http://localhost:8120 loadtest/carga.js
const VUS = Number(__ENV.VUS || 10);

export const options = {
  stages: [
    { duration: '15s', target: VUS },   // sobe a carga gradualmente
    { duration: '30s', target: VUS },   // mantém a carga
    { duration: '15s', target: 0 },     // desaquece
  ],
  thresholds: {
    http_req_failed:   ['rate<0.01'],   // meta: menos de 1% de falhas
    http_req_duration: ['p(95)<500'],   // meta: 95% das respostas < 500 ms
  },
};

export default function () {
  // 1. Healthcheck
  group('healthcheck', () => {
    const res = http.get(`${BASE}/ping`);
    check(res, { 'status 200': (r) => r.status === 200 });
  });

  // 2. Listagem de ocorrências (Leitura pública)
  group('list occurrences', () => {
    const res = http.get(`${BASE}/api/ocorrencias`);
    check(res, {
      'status 200': (r) => r.status === 200,
      'is list': (r) => Array.isArray(r.json()),
    });
  });

  // 3. Fluxo autenticado (Login, Perfil, Criação de Ocorrência)
  group('authenticated flow', () => {
    // Login usando form-urlencoded (padrão OAuth2 do backend)
    const loginPayload = {
      username: 'cidadao@exemplo.com',
      password: 'senha123',
    };
    const loginParams = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    };
    const loginRes = http.post(`${BASE}/api/auth/login`, loginPayload, loginParams);
    const loginOk = check(loginRes, {
      'login status 200': (r) => r.status === 200,
      'has token': (r) => r.json('access_token') !== undefined,
    });

    if (loginOk) {
      const token = loginRes.json('access_token');
      const authHeaders = {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      };

      // Consulta de Perfil
      const meRes = http.get(`${BASE}/api/auth/me`, authHeaders);
      check(meRes, {
        'me status 200': (r) => r.status === 200,
        'correct email': (r) => r.json('email') === 'cidadao@exemplo.com',
      });

      // Criação de Ocorrência (Escrita) com dados ligeiramente aleatórios para evitar colisões
      const randomId = Math.floor(Math.random() * 1000000);
      const lat = -7.1355 + (Math.random() - 0.5) * 0.01;
      const lng = -34.8421 + (Math.random() - 0.5) * 0.01;

      const occPayload = JSON.stringify({
        title: `Carga Teste #${randomId}`,
        category: 'infraestrutura',
        description: `Ocorrência gerada automaticamente pelo teste de carga k6. Lat: ${lat}, Lng: ${lng}`,
        lat: lat,
        lng: lng,
        photo: null,
        type: 'buracos em ruas',
      });

      const createRes = http.post(`${BASE}/api/ocorrencias`, occPayload, authHeaders);
      check(createRes, {
        'create status 201': (r) => r.status === 201,
        'created title correct': (r) => r.json('title').includes('Carga Teste'),
      });
    }
  });

  sleep(1);
}
