from typing import Literal

from pydantic import BaseModel, Field, model_validator


ResponseType = Literal[
    "stock_price",
    "stock_history",
    "stock_comparison",
    "company_research",
    "financial_news",
    "market_overview",
    "general_explanation",
]

ToolName = Literal[
    "get_stock_price",
    "get_stock_history",
    "compare_stocks",
    "compare_financial_metrics",
    "get_company_details",
    "get_financial_metrics",
    "get_financial_news",
    "get_market_overview",
]


class QueryPlan(BaseModel):
    intent: ResponseType
    entities: list[str] = Field(default_factory=list)
    region: Literal["US", "INDIA", "GLOBAL"] | None = None
    period: Literal["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"] | None = None
    required_tools: list[ToolName] = Field(default_factory=list)
    requires_live_data: bool = False
    canvas_action: Literal["add", "remove", "replace", "refresh"] | None = None
    requested_blocks: list[str] = Field(default_factory=list)


class HeadlineMetric(BaseModel):
    """The main value shown prominently by a query-specific frontend layout."""

    label: str
    value: str
    change: str | None = None
    context: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class Metric(BaseModel):
    name: str
    value: str
    change: str | None = None
    context: str | None = None
    ticker: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class Company(BaseModel):
    ticker: str
    name: str | None = None
    price: str | None = None
    currency: str | None = None
    change: str | None = None
    sector: str | None = None
    industry: str | None = None


class NewsItem(BaseModel):
    title: str
    publisher: str | None = None
    published_at: str | None = None
    summary: str | None = None
    url: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """A fact that directly supports an AI insight or summary statement."""

    claim: str
    metric: str
    value: str
    explanation: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class InsightCitation(BaseModel):
    text: str
    source_ids: list[str] = Field(default_factory=list)


class PerformanceTiming(BaseModel):
    planning_ms: float = 0
    tools_ms: float = 0
    provider_ms: float = 0
    total_ms: float = 0
    fast_path: bool = False
    model: str | None = None


class Source(BaseModel):
    id: str | None = None
    title: str
    url: str
    provider: str
    retrieved_at: str


class ToolCall(BaseModel):
    name: str
    arguments: dict


class ChartPoint(BaseModel):
    x: str
    y: float


class ChartSeries(BaseModel):
    name: str
    data: list[ChartPoint] = Field(default_factory=list)


class Chart(BaseModel):
    id: str
    type: Literal["line", "bar"]
    title: str
    x_axis: str
    y_axis: str
    unit: str | None = None
    series: list[ChartSeries] = Field(default_factory=list)


BlockType = Literal[
    "direct_answer",
    "headline",
    "headline_grid",
    "summary",
    "chart",
    "metric_grid",
    "company_grid",
    "insight_list",
    "evidence",
    "news_feed",
    "source_list",
    "tool_activity",
]
BlockSpan = Literal["full", "half", "one_third", "two_thirds"]
BlockVariant = Literal[
    "default",
    "price",
    "performance",
    "comparison",
    "compact",
    "featured",
]


class PresentationBlock(BaseModel):
    id: str
    type: BlockType
    data_ref: str
    span: BlockSpan = "full"
    variant: BlockVariant = "default"
    title: str | None = None


class PresentationPlan(BaseModel):
    layout: Literal[
        "compact",
        "research_dashboard",
        "comparison_dashboard",
        "news_digest",
        "market_dashboard",
        "explainer",
    ]
    blocks: list[PresentationBlock] = Field(default_factory=list)


class CanvasOperation(BaseModel):
    operation: Literal["add", "remove", "replace", "refresh"]
    block_type: BlockType
    block_id: str | None = None
    target_entity: str | None = None


class FinSightSynthesis(BaseModel):
    """Fields authored by Gemini from tool results."""

    response_type: ResponseType
    title: str
    direct_answer: str = ""
    summary: str
    headline: HeadlineMetric | None = None
    insights: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    news: list[NewsItem] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def preserve_legacy_answers(self) -> "FinSightSynthesis":
        # Saved responses and older provider payloads predate direct_answer.
        if not self.direct_answer.strip():
            self.direct_answer = self.summary
        return self


class FinSightResponse(FinSightSynthesis):
    research_id: str
    conversation_id: str | None = None
    canvas_id: str | None = None
    canvas_revision: int | None = None
    canvas_mode: Literal["full", "patch"] = "full"
    canvas_operations: list[CanvasOperation] = Field(default_factory=list)
    headlines: list[HeadlineMetric] = Field(default_factory=list)
    query_plan: QueryPlan | None = None
    summary_source_ids: list[str] = Field(default_factory=list)
    insight_citations: list[InsightCitation] = Field(default_factory=list)
    performance: PerformanceTiming | None = None
    query: str
    sources: list[Source] = Field(default_factory=list)
    charts: list[Chart] = Field(default_factory=list)
    presentation: PresentationPlan | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    generated_at: str
