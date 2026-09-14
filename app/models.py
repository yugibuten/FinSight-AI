from typing import Literal

from pydantic import BaseModel, Field


ResponseType = Literal[
    "stock_price",
    "stock_history",
    "stock_comparison",
    "company_research",
    "financial_news",
    "market_overview",
    "general_explanation",
]


class HeadlineMetric(BaseModel):
    """The main value shown prominently by a query-specific frontend layout."""

    label: str
    value: str
    change: str | None = None
    context: str | None = None


class Metric(BaseModel):
    name: str
    value: str
    change: str | None = None
    context: str | None = None
    ticker: str | None = None


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


class Evidence(BaseModel):
    """A fact that directly supports an AI insight or summary statement."""

    claim: str
    metric: str
    value: str
    explanation: str | None = None


class Source(BaseModel):
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
    "headline",
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


class FinSightSynthesis(BaseModel):
    """Fields authored by Gemini from tool results."""

    response_type: ResponseType
    title: str
    summary: str
    headline: HeadlineMetric | None = None
    insights: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    news: list[NewsItem] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class FinSightResponse(FinSightSynthesis):
    research_id: str
    query: str
    sources: list[Source] = Field(default_factory=list)
    charts: list[Chart] = Field(default_factory=list)
    presentation: PresentationPlan | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    generated_at: str
