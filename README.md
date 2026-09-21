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

FinSight's defining feature is its **dynamic financial website**. A user's query
does not simply fill a fixed answer template: it generates a purpose-built page
composition for that question. A stock-price request can become a compact price
view, a comparison can become a multi-company dashboard, a historical query can
lead with an interactive chart, and a news request can become a source-backed
news digest. The result is one application that adapts its content, hierarchy,
and presentation to the research being performed.

## Core feature: a website shaped by every query

Each answer is returned with a validated presentation manifest describing which
interface blocks should appear, their order, layout, visual variant, and
responsive width. The frontend uses this manifest to assemble the result from
reusable components such as:

- headline price cards
- metric and company grids
- interactive financial charts
- insight and supporting-evidence panels
- market and comparison dashboards
- financial news feeds
- source and tool-activity sections

This provides the experience of generating a financial website from a
natural-language command without allowing the model to execute arbitrary
frontend code.
Gemini creates and organizes the financial content, while the backend validates
the response and the frontend renders only allow-listed React components. This
keeps the experience dynamic, consistent, responsive, and safe.

### On-demand canvas commands

The generated research page persists throughout a conversation. Users can
modify it with natural-language commands instead of rebuilding the whole page:

```text
Also bring up the latest news on screen.
Add Tesla to this comparison.
Hide the supporting evidence.
Refresh the market metrics.
```

FinSight converts these requests into validated canvas operations. Add and
refresh commands retrieve any required financial data and merge only the
relevant blocks; remove commands can update the page without another Gemini
call. The frontend keeps the current page visible while the command runs and
briefly highlights changed sections when the new revision arrives.

Each canvas has an incrementing revision number. Clients send that revision
with their next command, preventing stale updates from silently overwriting
newer research. Applied canvas operations are stored as an audit trail.

## Features

- Natural-language research across stocks, companies, markets, and news
- Gemini-powered intent understanding, tool selection, and answer synthesis
- A validated query plan covering intent, entities, periods, tools, and UI blocks
- Current stock prices and daily price movement
- Historical price analysis and interactive charts
- Normalized performance comparisons for multiple stocks
- Company profiles and financial metrics
- Regional market overviews for US, Indian, and global markets
- Recent financial news with publisher and source links
- Evidence-backed summaries and insights
- Claim-level source IDs with clickable citations
- Deterministic CAGR, volatility, drawdown, and moving-average calculations
- A swappable market-data provider layer with Yahoo Finance as the default
- A dynamic website whose layout and components adapt to every query
- An on-demand canvas that can add, remove, replace, or refresh page sections
- Saved research history with reopen and delete support
- Context-aware conversations for follow-up research questions
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
selection is guided by a validated plan containing the detected intent,
companies, region, time period, live-data requirement, canvas action, and
expected page blocks. Tool results are then returned to the model for synthesis. Numeric chart data and
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
| `GEMINI_FAST_MODEL` | `gemini-3.5-flash` | Model used for simple synthesis |
| `GEMINI_COMPLEX_MODEL` | `gemini-3.5-flash` | Model used for comparisons and research |
| `REDIS_URL` | Unset | Optional shared cache connection URL |
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
| `POST` | `/api/v1/conversations` | Create an explicit research conversation |
| `GET` | `/api/v1/conversations` | List conversations |
| `GET` | `/api/v1/conversations/{conversation_id}` | Retrieve a conversation and its turns |
| `DELETE` | `/api/v1/conversations/{conversation_id}` | Delete a conversation and its turns |
| `GET` | `/api/v1/conversations/{conversation_id}/canvas` | Retrieve the current generated page |

Unversioned compatibility aliases are currently hidden from the OpenAPI schema.
New clients should always use `/api/v1`.

### Follow-up questions

The first query automatically creates a conversation and returns its
`conversation_id`. Send that identifier with a related follow-up:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question":"Compare it with Microsoft over the same period.",
    "conversation_id":"con_0123456789abcdef0123456789abcdef"
  }'
```

FinSight uses compact summaries of recent turns only when the wording depends on
earlier context. Standalone questions do not receive previous context, even when
they are stored in the same conversation. Starting a new research session in the
frontend clears the conversation boundary completely.

## Response model and dynamic interface

Each query returns a structured response containing:

- `response_type`, `title`, `summary`, and an optional primary `headline`
- `query_plan`, including detected entities, period, required tools, and canvas intent
- `insights`, `metrics`, and evidence connecting claims to supporting facts
- `companies` and `news` when relevant to the question
- deterministic `charts` generated from retrieved numeric data
- `sources` reconstructed from actual tool results
- `source_ids` connecting headlines, metrics, evidence, and news to those sources
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
| `compare_financial_metrics` | Compare valuation, growth, and profitability metrics |
| `get_company_details` | Retrieve company profile and classification data |
| `get_financial_metrics` | Retrieve valuation, growth, margin, cash, and debt metrics |
| `get_financial_news` | Retrieve recent company news and source links |
| `get_market_overview` | Retrieve major US, Indian, or global index movements |

Historical stock results also include deterministic analytics calculated from
daily closes: CAGR, annualized volatility, maximum drawdown, 20-day moving
average, and 50-day moving average. These values are calculated in Python and
are never estimated by Gemini.

Financial tools depend on a `MarketDataProvider` interface rather than importing
a vendor SDK directly. Yahoo Finance is the current adapter; another free or
commercial provider can be introduced without rewriting orchestration or tool
contracts.

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

### Performance pipeline

The validated query plan limits Gemini to only the tools relevant to the current
request. When all required arguments are known, FinSight executes those tools
before synthesis and runs independent calls concurrently. This removes the
model's initial tool-selection round trip for common queries. Direct stock-price
requests use a deterministic no-LLM fast path after retrieving verified data.

Simple and complex synthesis can use different Gemini models through
`GEMINI_FAST_MODEL` and `GEMINI_COMPLEX_MODEL`. Every response includes a
`performance` object with planning, tool, provider, and total processing times,
the selected model, and whether the fast path was used. The same information is
available in structured `query.performance` logs and the frontend tool-activity
panel.

The frontend presents progressive planning, data retrieval, and page-building
states while initial research runs. On-demand canvas changes retain the existing
page and show a targeted update state.

Failed tool results and API errors are not cached. Tool cache lifetimes reflect
the expected volatility of each data type, ranging from seconds for prices to
hours for company profiles. Without additional configuration, caches and rate
limiting remain process-local. Setting `REDIS_URL` enables Redis-backed response
and tool caches with automatic fallback to the local bounded cache if Redis is
unavailable. The rate limiter should use a shared implementation before a
multi-instance public deployment.

## Persistence and migrations

Every completed or failed query is recorded. Local development uses SQLite and
stores conversations, ordered research turns, structured results, and
tool-execution telemetry. The same SQLAlchemy layer supports PostgreSQL by
changing `DATABASE_URL`:

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
`evals/reports/latest.json`. Cases check answer completion, query planning, tool
selection, critical arguments, and required source evidence. The suite includes
price, history, market, news, movement explanation, risk analytics, Indian
symbols, and valuation-comparison cases.

## Data and security considerations

Yahoo Finance access through `yfinance` is unofficial and can be delayed,
incomplete, or rate-limited. FinSight is intended for financial research and
education, not trading execution or personalized financial advice. Important
financial information should always be verified against an authoritative source.

Never commit `.env`, API keys, database credentials, or other secrets to source
control.
