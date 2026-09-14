# FinSight

FinSight is an AI-powered financial intelligence platform for exploring stocks,
companies, markets, and financial news through natural-language questions. It
combines live market data with Gemini's reasoning and tool-calling capabilities
to produce structured, evidence-backed answers that can be presented as metrics,
charts, company cards, news feeds, and source lists.

The application is designed around a simple principle: financial explanations
should show the information supporting them. Instead of returning only an AI
opinion, FinSight pairs summaries and insights with the underlying market data,
supporting metrics, tool activity, and source links.

## Features

- Natural-language research across stocks, companies, markets, and news
- Gemini-powered intent understanding, tool selection, and answer synthesis
- Current stock prices and daily price movement
- Historical price analysis and interactive charts
- Normalized performance comparisons for multiple stocks
- Company profiles and financial metrics
- Regional market overviews for US, Indian, and global markets
- Recent financial news with publisher and source links
- Evidence-backed summaries and insights
- Query-specific layouts generated from a safe presentation manifest
- Saved research history with reopen and delete support
- Response and tool-result caching
- Structured request logging, stable error responses, rate limits, and timeouts
- Deterministic fallback answers when market data succeeds but AI synthesis fails

## How it works

```text
User question
     │
     ▼
Next.js assistant interface
     │
     ▼
FastAPI /api/v1/query
     │
     ▼
Query orchestrator ──► Gemini reasoning and tool selection
     │
     ├──► Stock tools
     ├──► Company tools
     ├──► News tools
     └──► Market tools
              │
              ▼
        Yahoo Finance data
              │
              ▼
Grounded synthesis, evidence, charts, and sources
              │
              ▼
Validated presentation manifest
              │
              ▼
Dynamic frontend components
```

Gemini determines which tools are needed and supplies their arguments. Tool
results are then returned to the model for synthesis. Numeric chart data and
source records are built deterministically from tool output rather than being
invented by the model.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Recharts |
| API | FastAPI, Pydantic |
| AI | Google Gemini through the `google-genai` SDK |
| Market data | Yahoo Finance through `yfinance` |
| Persistence | SQLAlchemy, Alembic, SQLite or PostgreSQL |
| Testing | pytest, TypeScript compiler, Next.js production build |

## Project structure

```text
app/
├── api/                 # Versioned routers and endpoint handlers
├── core/                # Configuration, caching, logging, errors, middleware
├── db/                  # SQLAlchemy models, database setup, repositories
├── schemas/             # Request and response schemas
├── tools/               # Stock, company, market, and news tools
├── main.py              # FastAPI application
├── models.py            # Financial and presentation response models
├── orchestrator.py      # Gemini workflow and deterministic processing
└── presentation.py      # Query-specific UI manifest builder

frontend/
├── app/                 # Next.js application shell and global styles
├── components/          # Query, history, result, and chart components
└── lib/                 # API client and TypeScript contracts

evals/                   # Live tool-selection evaluation cases and runner
migrations/              # Alembic database migrations
tests/                   # Mocked backend test suite
```

## Prerequisites

- Python 3.11 or newer
- Node.js and npm
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

Yahoo Finance access does not require an API key. `GEMINI_API_KEY` is the only
required external credential for the current application.

## Installation

Clone the repository and prepare the backend:

```bash
git clone <repository-url>
cd Qalytix-AI

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

On Windows, activate the environment with:

```powershell
venv\Scripts\activate
```

Add your Gemini API key to `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Install the frontend dependencies:

```bash
cd frontend
npm install
cp .env.local.example .env.local
cd ..
```

## Configuration

Backend settings are loaded from `.env` and validated at startup.

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Required | Gemini authentication |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Gemini model used for orchestration |
| `FRONTEND_ORIGINS` | Local frontend origins | Allowed CORS origins |
| `APP_ENVIRONMENT` | `development` | Runtime environment name |
| `QUERY_TIMEOUT_SECONDS` | `45` | Maximum query processing time |
| `PROVIDER_TIMEOUT_SECONDS` | `20` | Maximum AI provider call time |
| `RATE_LIMIT_REQUESTS` | `20` | Requests permitted during one window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window length |
| `MAX_REQUEST_BYTES` | `16384` | Maximum accepted request-body size |
| `RESPONSE_CACHE_SECONDS` | `30` | Full query-response cache lifetime |
| `DATABASE_URL` | `sqlite:///./data/finsight.db` | SQLAlchemy database connection URL |

The frontend reads `NEXT_PUBLIC_API_URL` from `frontend/.env.local` and uses
`http://127.0.0.1:8000` by default.

## Running the application

Start the backend from the repository root:

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Open the application at <http://localhost:3000>. API documentation is available
at <http://127.0.0.1:8000/docs>.

## API usage

Ask a question with `POST /api/v1/query`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How has Apple performed over the last 6 months?"}'
```

Example questions:

- `What is Apple's latest stock price?`
- `Compare Apple and Microsoft over the last year.`
- `How are Indian markets performing today?`
- `Show me the latest news about NVIDIA.`
- `What are Tesla's key financial metrics?`

Indian exchange symbols use Yahoo Finance suffixes such as `PAYTM.NS` and
`RELIANCE.NS`. Gemini can often infer the correct symbol, but an explicit ticker
is the most reliable input.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Check API availability and version |
| `POST` | `/api/v1/query` | Run a financial intelligence query |
| `GET` | `/api/v1/research` | List recent saved research |
| `GET` | `/api/v1/research/{research_id}` | Retrieve a complete saved result |
| `DELETE` | `/api/v1/research/{research_id}` | Delete saved research |

Unversioned compatibility aliases are currently hidden from the OpenAPI schema.
New clients should always use `/api/v1`.

## Response model and dynamic interface

Each query returns a structured response containing:

- `response_type`, `title`, `summary`, and an optional primary `headline`
- `insights`, `metrics`, and evidence connecting claims to supporting facts
- `companies` and `news` when relevant to the question
- deterministic `charts` generated from retrieved numeric data
- `sources` reconstructed from actual tool results
- `tool_calls` for auditability and evaluation
- a validated `presentation` plan describing block order, layout, and variants
- `research_id` and `generated_at` metadata

The presentation plan contains data references only; it cannot contain HTML,
JavaScript, or executable UI code. The frontend renders it through an allow-listed
React component registry. This gives price queries, comparisons, market reports,
news searches, and company research different interfaces while keeping rendering
predictable and safe.

Historical queries produce price line charts, comparisons produce normalized
percentage-performance charts, and market overviews produce daily-change bar
charts. Every chart also includes an expandable data table for accessibility.

## Financial data tools

| Tool | Purpose |
|---|---|
| `get_stock_price` | Retrieve the latest close and daily movement |
| `get_stock_history` | Retrieve historical prices and calculated performance |
| `compare_stocks` | Compare normalized performance for two to five stocks |
| `get_company_details` | Retrieve company profile and classification data |
| `get_financial_metrics` | Retrieve valuation, growth, margin, cash, and debt metrics |
| `get_financial_news` | Retrieve recent company news and source links |
| `get_market_overview` | Retrieve major US, Indian, or global index movements |

## Reliability and observability

FinSight includes several protections around the AI and data-provider workflow:

- validated environment configuration and request schemas
- request-size guards and process-local rate limiting
- query and provider timeouts
- stable, frontend-friendly error objects
- an `X-Request-ID` response header for tracing
- structured JSON logs for requests, cache events, tool calls, and provider errors
- bounded TTL caches for full responses and individual tool results
- deterministic synthesis fallback when tools succeed but Gemini is unavailable

Failed tool results and API errors are not cached. Tool cache lifetimes reflect
the expected volatility of each data type, ranging from seconds for prices to
hours for company profiles. The current caches and rate limiter are process-local;
a distributed deployment should use a shared store such as Redis.

## Persistence and migrations

Every completed or failed query is recorded. Local development uses SQLite and
stores research queries, structured results, and tool-execution telemetry. The
same SQLAlchemy layer supports PostgreSQL by changing `DATABASE_URL`:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/finsight
```

Migrations run automatically when the API starts. They can also be managed
manually:

```bash
alembic current
alembic upgrade head
alembic revision --autogenerate -m "describe the change"
```

Research records are not currently scoped to individual users. Add authentication
and ownership checks before exposing history or deletion endpoints publicly.

## Testing

Install the development dependencies and run the backend suite:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Validate and build the frontend:

```bash
cd frontend
npm run lint
npm run build
```

The automated tests mock external providers, so they are fast and do not consume
Gemini quota. Live evaluations are opt-in:

```bash
# Run one evaluation case
python -m evals.run_evals --case current_price_us

# Run a subset
python -m evals.run_evals --limit 3

# Run the complete evaluation set
python -m evals.run_evals
```

Evaluation cases live in `evals/cases.json`, and the latest report is written to
`evals/reports/latest.json`. Cases check answer completion, tool selection, and
critical tool arguments.

## Data and security considerations

Yahoo Finance access through `yfinance` is unofficial and can be delayed,
incomplete, or rate-limited. FinSight is intended for financial research and
education, not trading execution or personalized financial advice. Important
financial information should always be verified against an authoritative source.

Never commit `.env`, API keys, database credentials, or other secrets to source
control.
