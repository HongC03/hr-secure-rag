# PeopleVault — Secure HR RAG

A local demonstration of a secure HR Retrieval-Augmented Generation application. It uses only synthetic records and does **not** connect to a real payroll system or identity provider. Answer generation can use GPT or DeepSeek when configured.

## The security model

The application applies **authorisation before retrieval**:

```text
Authenticated identity → policy decision → permitted document set → retrieval → answer + citations
```

This ordering matters. Filtering after a vector search can leak sensitive content into model context, score/ranking signals, citations, caches, or logs. `AccessService.can_read()` is the application policy-enforcement point; it default-denies documents that do not match an explicit policy.

The query text is never copied into an audit event, regardless of whether it resembles an email, identifier, or payroll detail. Access decisions use document type, classification, and owner metadata rather than patterns found in the question. In this demo, those fields come from server-created records or local synthetic fixtures; a real ingestion path must assign and approve them independently of the uploader. The answer provider receives the question and only the retrieved authorised context. Prompt-like document text cannot grant new document access, although model output still requires validation before production use.

| Demo identity | May read | May not read |
| --- | --- | --- |
| Alice, employee | Her own payslip/tax statement; public HR guide | Anyone else's payroll or tax records |
| Marcus, manager | Manager leave guide; public HR guide | All payroll, tax, compensation, medical records |
| Priya, HR Payroll | Payroll/tax records and payroll runbook | Documents outside explicit policy (default deny) |
| Olivia, HR Partner | HR and manager policy documents | Payroll and tax records |

## Run locally

To start PostgreSQL, the Python API, and the built React frontend together:

```bash
test -f .env || cp .env.example .env
# On first use, replace both database passwords in .env with unique, strong values.
docker compose -f docker-compose.pgvector.yml up --build -d
docker compose -f docker-compose.pgvector.yml exec -T postgres psql -U postgres -d peoplevault -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/003_app_users.sql
docker compose -f docker-compose.pgvector.yml exec -T postgres psql -U postgres -d peoplevault -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/004_self_registration.sql
```

Open `http://127.0.0.1:5173` and create an employee account in the app. Registration assigns a separate generated account ID, so it cannot claim the ownership ID of an existing payslip. The new account can read general HR guides; an administrator must link it to private records. To use the seeded Alice, Marcus, Priya, or Olivia profiles, run `python3 scripts/manage_user.py alice --via-container` (replace `alice` as needed) and choose a password. The command stores only its salted hash in PostgreSQL. The frontend proxies `/api` to the backend container on port 8001. The backend waits for PostgreSQL, embeds the synthetic demo and Markdown fixture documents, then starts serving requests. The first build installs Python and Node dependencies and may take several minutes. The embedding model must be available from Hugging Face or an existing cache; optional cache and token settings are shown in `.env.example`.

To generate answers, set `LLM_PROVIDER=gpt` with `OPENAI_API_KEY`, or `LLM_PROVIDER=deepseek` with `DEEPSEEK_API_KEY` in `.env` before starting the backend. The default model and URL for each provider are defined in `backend/services/llm_config.py`. Only one provider is active at a time. The question and retrieved HR document text leave the backend for the selected provider, so use synthetic data unless that data transfer is approved. With no provider configured, questions with retrieved sources return `503`; questions with no authorised source still return the normal no-source answer.

Useful commands:

```bash
docker compose -f docker-compose.pgvector.yml ps
docker compose -f docker-compose.pgvector.yml logs -f backend
docker compose -f docker-compose.pgvector.yml stop
```

The PostgreSQL volume remains after `stop`. To run the backend directly on your machine instead:

```bash
cd hr-secure-rag
python3 -m pip install -r requirements-pgvector.txt
python3 app.py
```

Open `http://127.0.0.1:8001` and register or sign in. The direct Python app requires the same PostgreSQL account database. Administrator-provisioned Alice can retrieve her own synthetic payslip; Marcus cannot retrieve it; Priya can, because she is HR Payroll.

Run the policy checks:

```bash
python3 -m unittest test_app.py
```

## React frontend

The UI is a React + Vite application in `frontend/`. During development, start the Python API first, then in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally `http://127.0.0.1:5173`). Vite proxies `/api` calls to the Python service on port 8001, so browser code never owns the access-policy logic.

For a local build outside Docker, run `npm run build` from `frontend/`, then restart `python3 app.py`; the Python server detects and serves `frontend/dist` on port 8001. The Compose frontend is a separate Nginx service and rebuilds when you run `docker compose -f docker-compose.pgvector.yml up --build -d`. The backend writes UTC startup, request, and server-error logs to standard output; use `docker compose -f docker-compose.pgvector.yml logs -f backend` to follow them. Request logs include method, path, status, and duration, but omit query strings, headers, and bodies. Set `LOG_LEVEL` to `DEBUG`, `WARNING`, or `ERROR` to adjust verbosity (default: `INFO`).

## What makes it RAG

`llamaindex_authorised_retrieval()` creates a LlamaIndex `VectorStoreIndex` from only the policy-permitted corpus. `RagService.answer()` formats the retrieved documents with their IDs and asks the selected GPT or DeepSeek service to answer from that context. The local Google EmbeddingGemma model keeps retrieval local; enabling an answer provider sends the selected context to its API. A lexical relevance threshold prevents irrelevant vector results from becoming answers.

For production, use a self-hosted or contractually approved model endpoint, persist the index in an access-filtering vector store, and review model output for unsupported claims and prompt injection. The authorisation check must still happen before retrieval and answer generation. Retrieval follows the [LlamaIndex VectorStoreIndex guide](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/).

## Backend layout

- `app.py` — application entry point.
- `backend/controllers/` — request/use-case coordination.
- `backend/services/` — access policy, password hashing, query validation, metadata-only auditing, sessions, RAG orchestration, and separate GPT/DeepSeek answer providers.
- `backend/repositories/` — synthetic document storage and the optional pgvector adapter.
- `seed/` — synthetic demo identities and HR documents used by local tests and pgvector seeding; it must never contain real HR data.
- `backend/models.py` — shared response contracts.
- `backend/server.py` — thin HTTP/static React-bundle adapter.

## Accounts and pgvector persistence

`db/migrations/003_app_users.sql` creates the account table; `004_self_registration.sql` adds public employee registration with a separate `@username` login. PostgreSQL runs both automatically for a new volume. For an existing volume, apply both before rebuilding the backend:

```bash
docker compose -f docker-compose.pgvector.yml exec -T postgres psql -U postgres -d peoplevault -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/003_app_users.sql
docker compose -f docker-compose.pgvector.yml exec -T postgres psql -U postgres -d peoplevault -v ON_ERROR_STOP=1 -f /docker-entrypoint-initdb.d/004_self_registration.sql
```

The application database role can read accounts and insert employee accounts, but cannot update roles or passwords. The registration API accepts a username, full name, and password; it assigns an employee role and a random `self_...` user ID, and returns a `@username` login name. It ignores any client-supplied role or document owner ID. `scripts/manage_user.py --via-container` uses the running PostgreSQL container's local administrator socket to create or reset an account. Without that flag, the script connects directly using the local PostgreSQL administrator password from the ignored `.env` file and requires `psycopg` and `python-dotenv`. For an administrator-provisioned account, provide `--name`, `--role`, and `--department`; only an administrator running this script can assign a privileged role. Passwords are hashed with salted scrypt before insertion. The HTTP API never exposes password hashes.

Successful sign in creates an opaque, server-side session that expires after eight hours. The browser stores only an HTTP-only, SameSite=Strict cookie; it receives the Secure attribute when served over HTTPS. Sign out revokes the session. Sessions are process-local, so restarting the backend signs everyone out. Use HTTPS for any deployment beyond local development.

The normal direct Python demo uses an in-memory LlamaIndex unless pgvector is configured. The Compose stack configures the PostgreSQL/pgvector repository automatically; it filters by the app-authorised source IDs and PostgreSQL row-level security before cosine-distance ranking.

For direct Python development against the same database, install `requirements-pgvector.txt`, set `PGVECTOR_DATABASE_URL` or use the `.env` application password, and start `python3 app.py`. The Compose backend uses the `postgres` service name instead of `127.0.0.1` to reach the database.

The migration enables `vector`, stores 768-dimensional embeddings, adds an HNSW cosine-distance index, and enforces RLS by `app.user_id` and `app.user_role`. The application database role must be non-owner/non-superuser or PostgreSQL RLS can be bypassed. pgvector supports exact and approximate nearest-neighbour search in Postgres, and its own guidance recommends normal indexes alongside `WHERE` filters. [pgvector documentation](https://github.com/pgvector/pgvector)

The Compose backend seeds the synthetic Markdown files in `test_data/` automatically. For direct Python development or after editing those files outside Docker, run:

```bash
python3 scripts/seed_test_data.py
LOAD_TEST_DATA=1 python3 app.py
```

The seed command parses each Markdown file's metadata, applies the normal document chunking and EmbeddingGemma model, and upserts the vectors. Re-running it updates the same document IDs. The CSV payroll register is a reconciliation fixture and is not indexed because `payroll_register` is not an allowed document type. `LOAD_TEST_DATA=1` also loads the Markdown source IDs into the app's authorisation corpus; otherwise pgvector results from these files are filtered out before an answer.

`backend/orm_models.py` also provides a SQLAlchemy `HrDocumentChunk` mapping as a readable Python view of this table. The SQL migration remains authoritative, and `PgVectorRepository` remains the production access path because it sets the transaction-local RLS identity before querying.

### Document-aware chunking

Payslips and tax statements remain a single database row: their labels, amounts, and privacy context must never be separated. Long HR policies and payroll runbooks are split into overlapping word-based chunks during indexing. Each row preserves the source document identity (`parent_document_id`) and position (`chunk_index`). When retrieval finds a chunk, the service retrieves its immediate authorised neighbours before composing context. This improves answers that span a section boundary while ensuring both the in-app policy and PostgreSQL RLS apply to every added chunk.

Docker Compose automatically reads the Git-ignored `.env` file. Set separate strong values for `POSTGRES_PASSWORD` (the local PostgreSQL superuser) and `POSTGRES_APP_PASSWORD` (the application role). The application and the seed script also load `.env` automatically after the pgvector requirements are installed; an explicitly set `PGVECTOR_DATABASE_URL` takes precedence for deployments. `.env.example` is the only environment file intended for Git.

Changing either value after the PostgreSQL data volume has been initialized does not rotate the corresponding database role. Rotate the role separately, or recreate the local development volume if its data can be discarded.

## Production implementation required before real HR data

- Verified identity and employment status (for example through OIDC/SAML SSO), MFA, central session storage, login and registration throttling, and device/risk signals before using real HR data.
- Attribute-based access control backed by the HRIS: employee relationship, job function, region, legal entity, document type, and declared purpose of use.
- Encrypt documents and vector indexes with managed keys; separate tenant/legal-entity indexes; avoid cross-boundary backups and caches.
- Ingest through malware scanning, DLP/classification, independent approval of access labels, OCR quality checks, immutable versioning, retention schedules, and legal-hold controls.
- Enforce access filters inside the database/vector-store query itself, then perform a second policy check on each retrieved chunk before model context construction.
- Use an approved private model endpoint or self-hosted model; disable provider training/retention; redact and minimise prompts; prevent model/tool access to raw stores.
- Send tamper-evident, redacted audit events to the SIEM; alert on privilege changes, bulk retrieval, repeated denied requests, anomalous payroll access, and prompt injection.
- Conduct privacy-impact assessment, threat modelling, access reviews, red-team testing, audit review, UAT, and legal/security approvals before deployment.

## API

- `POST /api/login` — accepts `{ "userId": "alice", "password": "..." }` and sets a session cookie after checking the database hash.
- `POST /api/register` — accepts `{ "username": "newuser", "name": "New User", "password": "..." }`, creates an employee account, and sets a session cookie.
- `POST /api/logout` — revokes the current session and clears its cookie.
- `POST /api/ask` — secure RAG question. Requires a valid session cookie.
- `GET /api/audit` — available only to `hr_payroll` and `hr_partner` demo roles.
- `POST /api/documents` — synthetic payroll ingestion, limited to `hr_payroll`. With pgvector enabled, the API indexes the document before returning `201`; an indexing failure returns `503` and leaves the in-memory corpus unchanged. The source allowlist for API-created documents is still process-local, so these records need a persistent source registry before restart-safe retrieval is possible.
- `GET /api/health` and `GET /api/me`.
