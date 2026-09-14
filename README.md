# FinSight — Financial Intelligence MVP

FinSight is a FastAPI backend that lets Gemini select live stock-data tools,
executes those tools with yfinance, and synthesizes a grounded answer.

## Setup and run

Create a Gemini key at <https://aistudio.google.com/apikey>, then:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your key to .env
uvicorn app.main:app --reload
```

Swagger UI is at <http://127.0.0.1:8000/docs>. Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How has Apple performed over the last 6 months?"}'
```

The response is structured for query-specific frontend layouts and includes an
audit-friendly `tool_calls` list. Indian exchange symbols use Yahoo Finance
suffixes such as `PAYTM.NS`.

## Run the web interface

The application uses two local processes. Start the backend in the first
terminal:

```bash
cd /path/to/Qalytix-AI
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

FinSight V3 uses an AI-assistant workspace: research renders in a scrollable
conversation area while the query composer stays at the bottom for the next
question.

Start the frontend in a second terminal:

```bash
cd /path/to/Qalytix-AI/frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open <http://localhost:3000>. The frontend calls the FastAPI service at
`http://127.0.0.1:8000` by default. If the backend is hosted elsewhere, change
`NEXT_PUBLIC_API_URL` in `frontend/.env.local` and restart the frontend.

Useful frontend checks:

```bash
npm run lint
npm run build
```

## Phase 3 response contract

Every `/api/v1/query` response includes:

- `response_type` — tells the frontend which layout to render
- `title`, `summary`, and optional `headline` — primary AI presentation
- `insights` — concise interpretations grounded in tool results
- `metrics` and `evidence` — facts supporting the summary and insights
- `companies` and `news` — query-specific content collections
- `sources` — links rebuilt from actual tool results, not invented by the model
- `charts` — deterministic visualization series built from actual tool results
- `presentation` — a validated layout manifest containing safe block types,
  ordering, variants, and responsive spans
- `tool_calls` and `generated_at` — audit and freshness metadata

For example, a direct price query uses `response_type: "stock_price"` and a
compact headline such as Apple / $231.45 / +1.01%. A comparison query uses
`response_type: "stock_comparison"` and fills company, metric, and evidence
collections for a richer frontend layout.

### Dynamic UI

The backend now builds a query-specific `presentation` plan after Gemini has
produced the grounded content. A price lookup gets a compact price-first page,
a comparison gets a comparison dashboard, news gets a digest, and market or
company research gets a denser analytical layout.

The manifest contains data references only—it never contains HTML or executable
code. The frontend resolves each block through an allow-listed React component
registry. Unknown blocks or invalid chart references render nothing, and older
saved responses without a presentation plan use a backwards-compatible fallback.

### Financial charts

Historical queries return price line charts, comparisons return normalized
percentage-performance charts, and market overviews return daily-change bar
charts. Chart points are assembled by Python from tool output; Gemini does not
generate or modify the plotted numbers. The frontend uses Recharts for responsive
tooltips and legends and provides an expandable data table as an accessible
fallback.

## Available tools

- `get_stock_price` — latest close and daily move
- `get_stock_history` — historical prices and calculated performance
- `compare_stocks` — deterministic comparison of two to five stocks
- `get_company_details` — company profile, sector, industry, and exchange
- `get_financial_metrics` — valuation, growth, margins, cash, and debt
- `get_financial_news` — recent Yahoo Finance articles with source links
- `get_market_overview` — major US, Indian, or global index movements

All financial data tools currently use Yahoo Finance through `yfinance` and do
not require an additional API key. `GEMINI_API_KEY` is the only required key.

## Versioned API endpoints

- `GET /api/v1/health` — service liveness and API version
- `POST /api/v1/query` — accepts `{ "question": "..." }`

The old `/health` and `/query` paths are temporary compatibility aliases. They
are hidden from Swagger and will be removed after all clients migrate to v1.

## Backend safeguards

Backend configuration is validated from `.env` by `app/core/config.py`. The
defaults are suitable for local development and can be changed with:

```env
QUERY_TIMEOUT_SECONDS=45
PROVIDER_TIMEOUT_SECONDS=20
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
MAX_REQUEST_BYTES=16384
```

Each HTTP response includes an `X-Request-ID`. Application logs are emitted as
structured JSON with that ID, request duration, selected tools, and provider
status. Error responses use a stable frontend-friendly shape:

```json
{
  "error": {
    "code": "PROVIDER_RATE_LIMITED",
    "message": "The AI provider is temporarily rate limited. Please try again later.",
    "retryable": true,
    "request_id": "req_84f19a2c"
  }
}
```

The current rate limiter is process-local and intended for the MVP. A deployed
multi-instance service should replace it with a shared Redis-backed limiter.

## Caching

FinSight uses bounded, thread-safe in-memory TTL caches. Identical questions are
cached for 30 seconds by default, avoiding another Gemini request. Tool results
are cached independently according to how quickly each kind of data changes:

| Data | Cache lifetime |
|---|---:|
| Current stock price | 45 seconds |
| Market overview | 60 seconds |
| Financial news | 5 minutes |
| Price history | 15 minutes |
| Stock comparison | 15 minutes |
| Financial metrics | 6 hours |
| Company details | 24 hours |

Questions, tickers, ticker lists, and regions are normalized when forming cache
keys. Failed tool results and API errors are never cached. Set
`RESPONSE_CACHE_SECONDS=0` to disable full-response caching. Cache events are
included in the structured logs as `cache.hit`, `cache.miss`, `cache.expired`,
or `cache.stored`.

These caches are local to one backend process and reset whenever the server
restarts. Redis will replace them when FinSight is deployed across multiple
instances.

## Research persistence

FinSight saves every completed or failed query. Local development uses SQLite:

```env
DATABASE_URL=sqlite:///./data/finsight.db
```

The database contains `research_queries`, `research_results`, and
`tool_executions`. Stored tool telemetry includes arguments, success, duration,
and whether the tool result came from cache. The web interface lists recent
research and can reopen or delete a result without calling Gemini again.

History endpoints:

- `GET /api/v1/research` — list recent research
- `GET /api/v1/research/{research_id}` — reopen a full result and tool telemetry
- `DELETE /api/v1/research/{research_id}` — delete a result

Migrations run automatically when the API starts. They can also be managed
manually:

```bash
alembic current
alembic upgrade head
alembic revision --autogenerate -m "describe the change"
```

For PostgreSQL, install the existing requirements and change only the URL:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/finsight
```

The current history is shared by everyone using the backend. User ownership and
authorization will be added with authentication; do not expose deletion routes
publicly before then.

## Provider fallback

Gemini function calling may succeed while its final synthesis request is
temporarily unavailable. When at least one financial tool succeeded, FinSight
now returns a deterministic response assembled from that verified tool data
instead of discarding it with a 502 error. The response clearly notes that AI
synthesis was unavailable. If no tool produced usable data, the normal
provider error is returned.

This MVP is stateless. yfinance is an unofficial data source intended for
research/personal use and is suitable for a prototype, not production trading
decisions.

## Automated testing

Install development dependencies and run the free, mocked test suite:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Live LLM evaluations are opt-in because they call Gemini and Yahoo Finance:

```bash
# One smoke test
python -m evals.run_evals --case current_price_us

# First three cases
python -m evals.run_evals --limit 3

# Complete Phase 2 suite
python -m evals.run_evals
```

Live cases are defined in `evals/cases.json`. The latest result is written to
`evals/reports/latest.json`. A case passes when Gemini produces an answer,
selects the expected tools, and supplies the expected critical arguments.
