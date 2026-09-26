# PeopleVault — Secure HR RAG

A portfolio-quality, local demonstration of a privacy-first HR Retrieval-Augmented Generation application. It uses only synthetic records and deliberately does **not** connect to a real payroll system, identity provider, storage platform, or LLM.

## The security model

The application applies **authorisation before retrieval**:

```text
Authenticated identity → policy decision → permitted document set → retrieval → answer + citations
```

This ordering matters. Filtering after a vector search can leak sensitive content into model context, score/ranking signals, citations, caches, or logs. `AccessService.can_read()` is the application policy-enforcement point; it default-denies documents that do not match an explicit policy.

The query text is never copied into an audit event, regardless of whether it resembles an email, identifier, or payroll detail. Access decisions use document type, classification, and owner metadata rather than patterns found in the question. In this demo, those fields come from server-created records or local synthetic fixtures; a real ingestion path must assign and approve them independently of the uploader. This demo has no connected answer LLM or action tools, so prompt-like text cannot grant new document access. A future model integration still needs separate prompt-injection testing and output controls; a keyword filter alone is not an access policy.

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
```

Open `http://127.0.0.1:5173`. The frontend proxies `/api` to the backend container on port 8001. The backend waits for PostgreSQL, embeds the synthetic demo and Markdown fixture documents, then starts serving requests. The first build installs Python and Node dependencies and may take several minutes. The embedding model must be available from Hugging Face or an existing cache; optional cache and token settings are shown in `.env.example`.

Useful commands:

```bash
docker compose -f docker-compose.pgvector.yml ps
docker compose -f docker-compose.pgvector.yml logs -f backend
docker compose -f docker-compose.pgvector.yml stop
```

The PostgreSQL volume remains after `stop`. To run the backend directly on your machine instead:

```bash
cd hr-secure-rag
python3 -m pip install -r requirements.txt
python3 app.py
```

Open `http://127.0.0.1:8001`. Switch identities and ask the same payroll question. Alice can retrieve her own synthetic payslip; Marcus cannot retrieve it; Priya can, because she is HR Payroll.

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

For a local build outside Docker, run `npm run build` from `frontend/`, then restart `python3 app.py`; the Python server detects and serves `frontend/dist` on port 8001. The Compose frontend is a separate Nginx service and rebuilds when you run `docker compose -f docker-compose.pgvector.yml up --build -d`.

## What makes it RAG

`llamaindex_authorised_retrieval()` creates a LlamaIndex `VectorStoreIndex` from only the policy-permitted corpus; `langchain_answer()` uses LangChain LCEL primitives (`RunnableLambda` and `ChatPromptTemplate`) to construct context and the prompt. The local Google EmbeddingGemma model means no HR data leaves the device and the lexical relevance threshold prevents irrelevant vector results from becoming answers.

For production, replace the local embedder only with a self-hosted or contractually approved embedding endpoint, persist the index in an access-filtering vector store, and attach a private model gateway to the LangChain prompt chain. The authorisation check must still happen before either framework receives documents. The framework roles follow the [LlamaIndex VectorStoreIndex guide](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/) and [LangChain’s documented runnable/prompt composition model](https://docs.langchain.com/oss/python/langchain/overview).

## Backend layout

- `app.py` — application entry point.
- `backend/controllers/` — request/use-case coordination.
- `backend/services/` — access policy, query validation, metadata-only auditing, sessions, and LlamaIndex/LangChain RAG orchestration.
- `backend/repositories/` — synthetic document storage and the optional pgvector adapter.
- `seed/` — synthetic demo identities and HR documents used by local tests and pgvector seeding; it must never contain real HR data.
- `backend/models.py` — shared response contracts.
- `backend/server.py` — thin HTTP/static React-bundle adapter.

## pgvector persistence

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

- OIDC/SAML SSO, MFA, short-lived sessions, device/risk signals; never use the demo identity switch.
- Attribute-based access control backed by the HRIS: employee relationship, job function, region, legal entity, document type, and declared purpose of use.
- Encrypt documents and vector indexes with managed keys; separate tenant/legal-entity indexes; avoid cross-boundary backups and caches.
- Ingest through malware scanning, DLP/classification, independent approval of access labels, OCR quality checks, immutable versioning, retention schedules, and legal-hold controls.
- Enforce access filters inside the database/vector-store query itself, then perform a second policy check on each retrieved chunk before model context construction.
- Use an approved private model endpoint or self-hosted model; disable provider training/retention; redact and minimise prompts; prevent model/tool access to raw stores.
- Send tamper-evident, redacted audit events to the SIEM; alert on privilege changes, bulk retrieval, repeated denied requests, anomalous payroll access, and prompt injection.
- Conduct privacy-impact assessment, threat modelling, access reviews, red-team testing, audit review, UAT, and legal/security approvals before deployment.

## API

- `POST /api/login` — creates a **demo-only** session for a synthetic identity.
- `POST /api/ask` — secure RAG question. Requires `X-Demo-Session`.
- `GET /api/audit` — available only to `hr_payroll` and `hr_partner` demo roles.
- `POST /api/documents` — synthetic payroll ingestion, limited to `hr_payroll`. With pgvector enabled, the API indexes the document before returning `201`; an indexing failure returns `503` and leaves the in-memory corpus unchanged. The source allowlist for API-created documents is still process-local, so these records need a persistent source registry before restart-safe retrieval is possible.
- `GET /api/health` and `GET /api/me`.
