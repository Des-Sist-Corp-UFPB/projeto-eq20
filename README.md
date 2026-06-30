# 🏙️ RIOU - Registro Inteligente de Ocorrências Urbanas

O **RIOU** (Registro Inteligente de Ocorrências Urbanas) é uma plataforma web moderna projetada para permitir que cidadãos reportem e acompanhem ocorrências e problemas em sua cidade (como buracos em vias públicas, vazamentos de água, postes sem luz e incidentes de segurança). O sistema permite que administradores públicos gerenciem essas demandas de forma prioritária e transparente.

A plataforma utiliza um modelo dinâmico de pontuação de urgência baseado na quantidade de pessoas afetadas e no tempo decorrido, garantindo que os problemas mais críticos sejam resolvidos primeiro.

---

## 🚀 Principais Funcionalidades

### 👥 Para o Cidadão
- **Registro de Ocorrências:** Cadastro rápido de problemas com título, categoria, descrição, coordenadas no mapa (latitude e longitude) e fotos explicativas.
- **Modo Anônimo ou Identificado:** Possibilidade de enviar relatos de forma totalmente anônima ou autenticada.
- **Apoio a Ocorrências (Afetado):** Usuários cadastrados podem sinalizar que também são afetados por uma determinada ocorrência criada por outro cidadão, aumentando o peso daquele problema.
- **Interface Responsiva & PWA:** Totalmente adaptado para dispositivos móveis com suporte a Progressive Web App (PWA).

### 🛠️ Para a Administração Pública
- **Painel Administrativo Pro:** Visualização detalhada de ocorrências ordenadas dinamicamente pela relevância.
- **Ordenação por Gravidade (Urgency Score):** O sistema calcula automaticamente a urgência:
  $$\text{Urgency Score} = \text{Tempo desde a criação (horas)} + (\text{Quantidade de pessoas afetadas} \times 24)$$
- **Gerenciamento de Status:** Atualização de ocorrências para *Pendente*, *Em Progresso*, *Resolvido* ou *Rejeitado*.
- **Moderação de Usuários:** Capacidade de banir temporariamente (com tempo de expiração) ou excluir usuários infratores.
- **Resolução em Lote (Batch Resolve):** Opção rápida para resolver múltiplas ocorrências pendentes de uma só vez.
- **Logs de Auditoria (Audit Log):** Monitoramento completo e seguro das atividades de administração, como login de usuários, alteração de configurações e banimentos.
- **Feature Toggles:** Controle em tempo real do comportamento do sistema:
  - `allow_personal_occurrences`: Habilita ou desabilita a criação de ocorrências de segurança pessoal/pública.
  - `read_only_mode`: Coloca o sistema inteiro em modo somente leitura.
  - `allow_mock_photos`: Permite o uso de fotos mockadas caso necessário.

---

## 🛠️ Stack Tecnológica

O RIOU foi construído sobre uma arquitetura moderna e dividida em microsserviços/camadas:

* **Frontend:** [Vue 3](https://vuejs.org/) (Single Page Application com Composition API e `<script setup>`), construído com [Vite](https://vitejs.dev/) e suporte a **PWA**.
* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13) robusto, performático, assíncrono e autodocumentado com Swagger/OpenAPI.
* **Banco de Dados:** [PostgreSQL 16](https://www.postgresql.org/) para persistência relacional.
* **Armazenamento de Fotos (Object Storage):** Integração com **AWS S3 / MinIO** para upload de fotos das ocorrências.
* **E-mails de Verificação:** Integração com a API do **Resend** para envio seguro de códigos de verificação no cadastro.
* **Containerização:** [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/) para orquestração fácil de ambientes de desenvolvimento e produção.

---

## 📁 Estrutura de Diretórios

```text
projeto-eq20/
├── backend/                  # Código fonte do servidor FastAPI
│   ├── app/
│   │   ├── config/           # Configurações centralizadas (settings.py)
│   │   ├── database/         # Sessão do SQLAlchemy, seed e migração do BD
│   │   ├── models/           # Modelos de dados (User, Ocorrencia, AuditLog, etc.)
│   │   ├── repositories/     # Abstração de persistência/acesso ao banco
│   │   ├── routers/          # Endpoints da API (/auth, /ocorrencias, /admin)
│   │   ├── schemas/          # Schemas de validação de dados do Pydantic
│   │   ├── security/         # Criptografia, hashes e dependências de autenticação
│   │   └── services/         # Regras de negócio e integrações (S3, Resend)
│   ├── main.py               # Ponto de entrada / proxy imports
│   ├── requirements.txt      # Dependências Python
│   └── test_api.py           # Suíte de testes automatizados com pytest
│
├── frontend/                 # Aplicação web Vue.js
│   ├── src/
│   │   ├── assets/           # Arquivos estáticos (imagens, logotipos, etc.)
│   │   ├── components/       # Componentes Vue reutilizáveis
│   │   ├── App.vue           # Interface e lógica principal da SPA
│   │   ├── main.js           # Inicialização da aplicação
│   │   └── style.css         # Design System e estilização vanilla CSS
│   ├── package.json          # Script de builds e dependências do Node.js
│   └── vite.config.js        # Configuração do empacotador Vite
│
├── Dockerfile                # Build multi-stage unificado (Vue + FastAPI)
├── docker-compose.yml        # Setup do ambiente local completo (App + DB)
└── docker-compose.prod.yml   # Setup voltado para produção/homologação
```

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` na raiz do diretório `backend` (ou passe via docker-compose) para configurar a aplicação:

```env
# URL de Conexão com o PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/riou

# Chave secreta para assinatura dos tokens JWT
SECRET_KEY=sua_chave_secreta_aqui

# Credenciais e Endpoints do Object Storage (S3 / MinIO)
S3_ENDPOINT_URL=https://s3.dsc.rodrigor.com
S3_PUBLIC_ENDPOINT=https://s3.dsc.rodrigor.com
S3_BUCKET=eq20
S3_ACCESS_KEY=eq20
S3_SECRET_KEY=sua_secret_key_s3
S3_REGION=us-east-1

# Credenciais do Resend para envio de e-mails
RESEND_API_KEY=re_sua_api_key_do_resend
RESEND_FROM_EMAIL=verificacao@riou <onboarding@resend.dev>
```

---

## 🚀 Como Executar o Projeto

### Método 1: Utilizando Docker Compose (Recomendado)

O Docker Compose automatiza toda a configuração, gerando o banco de dados PostgreSQL e construindo o backend e frontend (multi-stage build) de uma só vez.

1. Garanta que o Docker e Docker Compose estão instalados e rodando.
2. Na raiz do projeto, execute o comando:
   ```bash
   docker compose up --build
   ```
3. O sistema estará disponível em:
   - **Frontend & Backend unificados:** [http://localhost:8120](http://localhost:8120)
   - **Documentação Interativa da API (Swagger):** [http://localhost:8120/docs](http://localhost:8120/docs)

---

### Método 2: Inicialização Manual (Desenvolvimento Local)

Para fins de desenvolvimento e hot-reloading rápido, você pode rodar o backend e o frontend separadamente em terminais distintos.

#### 1. Configurando o Backend (FastAPI)
1. Navegue até a pasta `backend`:
   ```bash
   cd backend
   ```
2. Crie e ative um ambiente virtual:
   * **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Instale as dependências requeridas:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute o servidor de desenvolvimento:
   ```bash
   uvicorn main:app --reload --port 8080
   ```
   *O backend estará rodando em [http://localhost:8080](http://localhost:8080).*

#### 2. Configurando o Frontend (Vue 3 + Vite)
1. Abra outro terminal na pasta `frontend`:
   ```bash
   cd frontend
   ```
2. Instale os pacotes npm:
   ```bash
   npm install
   ```
3. Execute o servidor do Vite:
   ```bash
   npm run dev
   ```
   *O frontend estará rodando em [http://localhost:5173](http://localhost:5173).*

---

## 🧪 Rodando os Testes

Os testes cobrem a lógica de negócios, endpoints, simulação de uploads de arquivos, banimentos, logs de auditoria e regras de urgência.

Para rodar a suíte completa de testes no backend:
1. Certifique-se de que está na pasta `backend` e com o ambiente virtual ativo.
2. Execute o comando:
   ```bash
   pytest -v
   ```

### 📊 Cobertura de Testes (≥ 85%)

O projeto possui **90%** de cobertura de linhas nos testes automatizados do backend.

O relatório de cobertura completo gerado em HTML está localizado em:
* [cobertura/backend/index.html](cobertura/backend/index.html)

---

## 🔑 Credenciais Padrão (Seed de Banco de Dados)

Ao inicializar o banco de dados pela primeira vez, ele é automaticamente populado com as seguintes credenciais padrão para facilitar a experimentação:

| Perfil | E-mail | Senha |
| :--- | :--- | :--- |
| **Administrador** | `admin@riou.com` | `admin123` |
| **Cidadão Comum** | `cidadao@exemplo.com` | `senha123` |

Além disso, 4 ocorrências mockadas em diferentes áreas (infraestrutura, iluminação, segurança e saneamento) serão criadas para que o mapa e a listagem administrativa tenham dados visuais de teste desde o primeiro login.

---

## 📝 Log de Auditoria

O sistema possui um módulo completo de auditoria para registrar ações críticas dos usuários, com foco especial em ações administrativas e de segurança.

### O que é auditado
São auditadas as seguintes ações do sistema:
* **Autenticação e Cadastro**:
  * `REGISTER`: Cadastro e ativação de novos cidadãos.
  * `LOGIN`: Login de usuários no sistema.
  * `PASSWORD_FORGOT`: Solicitação de recuperação de senha.
  * `PASSWORD_RESET`: Redefinição de senha utilizando o token.
* **Ações Administrativas**:
  * `ADMIN_TOGGLE_UPDATE`: Alteração de estado de Feature Toggles (ex: modo somente leitura).
  * `ADMIN_BATCH_RESOLVE`: Resolução de ocorrências em lote.
  * `ADMIN_DELETE_USER`: Exclusão de usuários da plataforma.
  * `ADMIN_BAN_USER` / `ADMIN_UNBAN_USER`: Banimento temporário e desbanimento de usuários.

### Onde fica armazenado
Os logs são persistidos no banco de dados relacional (PostgreSQL) na tabela **`audit_logs`**.
Os principais campos da tabela são:
* `id` (Integer, Chave Primária): Identificador único do log.
* `timestamp` (DateTime com Timezone): Data e hora em que a ação ocorreu (UTC).
* `user_id` (Integer, FK para `users.id`): Identificador do usuário que realizou a ação (com `ondelete="SET NULL"` para manter o histórico caso o usuário seja excluído).
* `user_email` (String): E-mail do usuário no momento da ação (redundância útil para auditorias históricas).
* `action` (String): O nome da ação executada (ex: `LOGIN`, `ADMIN_BAN_USER`).
* `resource` (String): O recurso afetado (ex: `user`, `feature_toggle`, `ocorrencia`).
* `resource_id` (String): O identificador do recurso afetado.
* `details` (Text): Detalhes adicionais legíveis por humanos sobre a ação.

### Como foi implementado
A auditoria foi implementada através de um **serviço dedicado** (`AuditLogService`), que utiliza o padrão de **Repositório** (`AuditLogRepository`) para persistir os registros de auditoria de forma isolada do fluxo principal das operações de negócio. Quando as ações críticas de negócio são disparadas no `AuthService` ou no `AdminService`, esses serviços invocam explicitamente o `AuditLogService` para registrar a entrada correspondente.

### Classes e arquivos participantes
* **Modelo do Banco de Dados**: [backend/app/models/audit_log.py](backend/app/models/audit_log.py)
* **Abstração de Acesso a Dados (Repositório)**: [backend/app/repositories/audit_log_repository.py](backend/app/repositories/audit_log_repository.py)
* **Serviço de Auditoria**: [backend/app/services/audit_log_service.py](backend/app/services/audit_log_service.py)
* **Pontos de Invocação**:
  * [backend/app/services/auth_service.py](backend/app/services/auth_service.py) (Ações de autenticação e recuperação/reset de senha)
  * [backend/app/services/admin_service.py](backend/app/services/admin_service.py) (Ações administrativas, controle de toggles, banimentos e exclusões)
* **Schemas Pydantic**: [backend/app/schemas/audit_log.py](backend/app/schemas/audit_log.py)
* **Rotas da API**: [backend/app/routers/admin.py](backend/app/routers/admin.py) (Endpoint `/api/admin/audit-logs` para visualização dos logs pelo administrador)

---

## 🔌 Integração com Serviço Externo

O sistema integra-se com dois serviços externos fundamentais para o armazenamento de mídias e para a verificação de e-mails.

### 1. Object Storage (AWS S3 / MinIO)
* **Para que é usado**: Armazenamento de fotos enviadas pelos cidadãos no momento do cadastro de uma ocorrência urbana.
* **Classes e arquivos participantes**:
  * [backend/app/services/storage_service.py](backend/app/services/storage_service.py): Contém as funções de inicialização do cliente S3, verificação/criação automática do bucket e upload do arquivo para o S3.
  * [backend/app/routers/ocorrencias.py](backend/app/routers/ocorrencias.py): Endpoint `/api/ocorrencias/upload` que recebe a imagem e delega o upload ao `storage_service.py`.
* **Como é configurado**:
  Através das seguintes variáveis de ambiente (localizadas no arquivo `.env` do backend):
  * `S3_ENDPOINT_URL`: URL do endpoint do serviço S3 (ex: `https://s3.dsc.rodrigor.com` em desenvolvimento local, ou `http://minio:9000` via Docker).
  * `S3_PUBLIC_ENDPOINT`: URL pública para acesso direto e visualização das imagens via navegador.
  * `S3_BUCKET`: Nome do bucket onde as imagens são salvas.
  * `S3_ACCESS_KEY`: Chave de acesso do S3.
  * `S3_SECRET_KEY`: Chave secreta de autenticação do S3.
  * `S3_REGION`: Região da AWS (padrão `us-east-1`).

### 2. Resend (Envio de E-mails)
* **Para que é usado**: Envio seguro de e-mails com códigos de verificação de uso único no cadastro de cidadãos, garantindo a autenticidade e validade dos endereços de e-mail informados.
* **Classes e arquivos participantes**:
  * [backend/app/services/email_service.py](backend/app/services/email_service.py): Implementa a chamada HTTP à API REST da Resend (`https://api.resend.com/emails`) utilizando a biblioteca `httpx` de forma síncrona.
  * [backend/app/services/auth_service.py](backend/app/services/auth_service.py): Invoca a geração do código pendente e aciona o envio de e-mail ao registrar o usuário.
* **Como é configurado**:
  Através das seguintes variáveis de ambiente:
  * `RESEND_API_KEY`: Chave de API do serviço Resend (`re_...`). Possui mecanismo de fallback automático: se a chave estiver vazia ou iniciar com `mock_`, o e-mail não é enviado e o código de verificação é apenas impresso nos logs do Docker para desenvolvimento/depuração.
  * `RESEND_FROM_EMAIL`: O endereço de remetente configurado e autorizado para envio no Resend (ex: `verificacao@riou <onboarding@resend.dev>`).