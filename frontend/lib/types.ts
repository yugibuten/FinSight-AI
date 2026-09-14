export type ResponseType =
  | "stock_price"
  | "stock_history"
  | "stock_comparison"
  | "company_research"
  | "financial_news"
  | "market_overview"
  | "general_explanation";

export interface HeadlineMetric {
  label: string;
  value: string;
  change?: string | null;
  context?: string | null;
}

export interface Metric {
  name: string;
  value: string;
  change?: string | null;
  context?: string | null;
  ticker?: string | null;
}

export interface Company {
  ticker: string;
  name?: string | null;
  price?: string | null;
  currency?: string | null;
  change?: string | null;
  sector?: string | null;
  industry?: string | null;
}

export interface NewsItem {
  title: string;
  publisher?: string | null;
  published_at?: string | null;
  summary?: string | null;
  url?: string | null;
}

export interface Evidence {
  claim: string;
  metric: string;
  value: string;
  explanation?: string | null;
}

export interface Source {
  title: string;
  url: string;
  provider: string;
  retrieved_at: string;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface ChartPoint {
  x: string;
  y: number;
}

export interface ChartSeries {
  name: string;
  data: ChartPoint[];
}

export interface Chart {
  id: string;
  type: "line" | "bar";
  title: string;
  x_axis: string;
  y_axis: string;
  unit?: string | null;
  series: ChartSeries[];
}

export type PresentationBlockType =
  | "headline"
  | "summary"
  | "chart"
  | "metric_grid"
  | "company_grid"
  | "insight_list"
  | "evidence"
  | "news_feed"
  | "source_list"
  | "tool_activity";

export interface PresentationBlock {
  id: string;
  type: PresentationBlockType;
  data_ref: string;
  span: "full" | "half" | "one_third" | "two_thirds";
  variant: "default" | "price" | "performance" | "comparison" | "compact" | "featured";
  title?: string | null;
}

export interface PresentationPlan {
  layout:
    | "compact"
    | "research_dashboard"
    | "comparison_dashboard"
    | "news_digest"
    | "market_dashboard"
    | "explainer";
  blocks: PresentationBlock[];
}

export interface FinSightResponse {
  research_id: string;
  query: string;
  response_type: ResponseType;
  title: string;
  summary: string;
  headline?: HeadlineMetric | null;
  insights: string[];
  metrics: Metric[];
  companies: Company[];
  news: NewsItem[];
  evidence: Evidence[];
  sources: Source[];
  charts: Chart[];
  presentation?: PresentationPlan | null;
  tool_calls: ToolCall[];
  generated_at: string;
}

export interface ResearchListItem {
  id: string;
  question: string;
  response_type?: string | null;
  status: string;
  response_cache_hit: boolean;
  duration_ms?: number | null;
  error_code?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ResearchDetail extends ResearchListItem {
  result?: FinSightResponse | null;
}
