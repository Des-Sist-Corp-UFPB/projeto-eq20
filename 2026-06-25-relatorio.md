# Relatório de Avaliação — EQ20 (DSC)

| | |
|---|---|
| **Data** | 2026-06-25 |
| **Repositório** | https://github.com/des-sist-corp-ufpb/projeto-eq20 |
| **Aplicação** | https://eq20.dsc.rodrigor.com |
| **Período de atividade** | 2026-06-19 → 2026-06-25 |
| **Total de commits** (sem merges, branch main) | 2 |
| **Integrantes** | Gabriel Calaca Machado (@crowdN), Joao Olivio Do Nascimento Filho (@olivionasc) |

---

## 1. Tecnologias

- Python
- FastAPI
- SQLAlchemy
- pytest

---

## 2. Análise Funcional

### Endpoints REST (19 mapeados)

| Método | Path | Arquivo |
|--------|------|---------|
| `DELETE` | `/users/{user_id}` | `admin.py` |
| `GET` | `/audit-logs` | `admin.py` |
| `GET` | `/toggles` | `admin.py` |
| `GET` | `/users` | `admin.py` |
| `POST` | `/batch-resolve` | `admin.py` |
| `POST` | `/toggles` | `admin.py` |
| `POST` | `/users/{user_id}/ban` | `admin.py` |
| `GET` | `/me` | `auth.py` |
| `POST` | `/forgot-password` | `auth.py` |
| `POST` | `/login` | `auth.py` |
| `POST` | `/register` | `auth.py` |
| `POST` | `/reset-password` | `auth.py` |
| `POST` | `/verify-register` | `auth.py` |
| `GET` | `/ping` | `main.py` |
| `GET` | `/{catchall:path}` | `main.py` |
| `DELETE` | `/{ocorrencia_id}` | `ocorrencias.py` |
| `PATCH` | `/{ocorrencia_id}/status` | `ocorrencias.py` |
| `POST` | `/upload` | `ocorrencias.py` |
| `POST` | `/{ocorrencia_id}/toggle-afetado` | `ocorrencias.py` |

### Entidades / Tabelas (5 encontradas)

- `audit_logs`
- `pending_registrations`
- `users`
- `feature_toggles`
- `ocorrencias`

---

## 3. Análise Arquitetural

| Aspecto | Status | Observação |
|---------|--------|-----------|
| Arquitetura em camadas | ✅ | controller=✅  service=✅  repository=✅ |
| Testes automatizados | ✅ | 1 arquivo(s) de teste |
| Migrations versionadas | ❌ | não encontradas |
| Logging | ❌ | não detectado |
| Autenticação / Segurança | ✅ | Spring Security / JWT / decorator detectado |
| DTOs / Separação de dados | ❌ | não detectado |
| Tratamento global de exceções | ❌ | não detectado |
| Documentação de API (OpenAPI) | ❌ | não detectado |
| Variáveis de ambiente | ✅ | .env / @Value / os.environ detectado |
| Dockerfile / docker-compose | ✅ | presente |

---

## 4. Contribuição por Usuário

### Resumo

| Usuário | Commits (main) | Commits (GitHub API) | Linhas adicionadas | Linhas no código atual | % código atual |
|---------|---------------|---------------------|-------------------|----------------------|----------------|
| Gabriel Calaca Machado (@crowdN) | 1 | **7** ⚠️ | 15.143 | 5.179 | 100% |
| Joao Olivio Do Nascimento Filho (@olivionasc) | 0 | **19** ⚠️ | 0 | 0 | 0% |
| *(sem login GitHub)* | 1 | 50% | — | — | — |

> **⚠️ Divergência entre commits locais e GitHub API:**
> - **@crowdN**: 1 commit(s) na branch `main` vs **7** registrados na API GitHub (commits em branches não mergeadas ou absorvidos via squash-merge sem preservação de autoria).
> - **@olivionasc**: 0 commit(s) na branch `main` vs **19** registrados na API GitHub (commits em branches não mergeadas ou absorvidos via squash-merge sem preservação de autoria).
>

### Contribuição por Camada

| Camada | Total linhas | Gabriel Calaca Machado (@crowdN) | Joao Olivio Do Nascimento Filho (@olivionasc) |
|--------|-------------|---------|---------|
| Controller | 271 | 100% | 0% |
| Frontend | 1.853 | 100% | 0% |
| Repository | 309 | 100% | 0% |
| Service | 801 | 100% | 0% |
| Test | 909 | 100% | 0% |

---

## 5. Contribuição por Funcionalidade

Baseado em `git blame` nos arquivos de controller e service.

| Arquivo | Total linhas | Gabriel Calaca Machado (@crowdN) | Joao Olivio Do Nascimento Filho (@olivionasc) |
|---------|-------------|---------|---------|
| `ocorrencia_service.py` | 274 | 100% | 0% |
| `auth_service.py` | 238 | 100% | 0% |
| `admin_service.py` | 130 | 100% | 0% |
| `ocorrencias.py` | 122 | 100% | 0% |
| `admin.py` | 86 | 100% | 0% |
| `email_service.py` | 64 | 100% | 0% |
| `auth.py` | 62 | 100% | 0% |
| `storage_service.py` | 58 | 100% | 0% |
| `audit_log_service.py` | 36 | 100% | 0% |
| `__init__.py` | 2 | 100% | 0% |

---

*Relatório gerado automaticamente em 2026-06-25.*
*Os dados de contribuição são baseados em `git log --numstat` (linhas adicionadas) e `git blame` (linhas no código atual), excluindo commits de merge.*