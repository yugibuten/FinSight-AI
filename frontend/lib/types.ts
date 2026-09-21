export type ResponseType =
  | "stock_price"
  | "stock_history"
  | "stock_comparison"
  | "company_research"
  | "financial_news"
  | "market_overview"
  | "general_explanation";

export interface QueryPlan {
  intent: ResponseType;
  entities: string[];
  region?: "US" | "INDIA" | "GLOBAL" | null;
  period?: "5d" | "1mo" | "3mo" | "6mo" | "1y" | "2y" | "5y" | null;
  required_tools: string[];
  requires_live_data: boolean;
  canvas_action?: "add" | "remove" | "replace" | "refresh" | null;
  requested_blocks: string[];
}

export interface PerformanceTiming {
  planning_ms: number;
  tools_ms: number;
  provider_ms: number;
  total_ms: number;
  fast_path: boolean;
  model?: string | null;
}

export interface HeadlineMetric {
  label: string;
  value: string;
  change?: string | null;
  context?: string | null;
  source_ids?: string[];
}

export interface Metric {
  name: string;
  value: string;
  change?: string | null;
  context?: string | null;
  ticker?: string | null;
  source_ids?: string[];
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
  source_ids?: string[];
}

export interface Evidence {
  claim: string;
  metric: string;
  value: string;
  explanation?: string | null;
  source_ids?: string[];
}

export interface InsightCitation {
  text: string;
  source_ids: string[];
}

export interface Source {
  id?: string | null;
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
  | "direct_answer"
  | "headline"
  | "headline_grid"
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

export interface CanvasOperation {
  operation: "add" | "remove" | "replace" | "refresh";
  block_type: PresentationBlockType;
  block_id?: string | null;
  target_entity?: string | null;
}

export interface FinSightResponse {
  research_id: string;
  conversation_id?: string | null;
  canvas_id?: string | null;
  canvas_revision?: number | null;
  canvas_mode?: "full" | "patch";
  canvas_operations?: CanvasOperation[];
  query_plan?: QueryPlan | null;
  performance?: PerformanceTiming | null;
  query: string;
  response_type: ResponseType;
  title: string;
  direct_answer?: string;
  summary: string;
  summary_source_ids?: string[];
  headline?: HeadlineMetric | null;
  headlines?: HeadlineMetric[];
  insights: string[];
  insight_citations?: InsightCitation[];
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

export interface MarketTickerItem {
  name: string;
  symbol: string;
  price?: number | null;
  currency?: string | null;
  change_percent?: number | null;
  as_of?: string | null;
  available: boolean;
}

export interface MarketTickerSnapshot {
  label: string;
  delayed: boolean;
  items: MarketTickerItem[];
  generated_at: string;
}

export interface ResearchListItem {
  id: string;
  conversation_id?: string | null;
  turn_index?: number | null;
  question: string;
  response_type?: string | null;
  status: string;
  response_cache_hit: boolean;
  duration_ms?: number | null;
  error_code?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ConversationListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  turn_count: number;
}

export interface ConversationTurn {
  research_id: string;
  turn_index: number;
  question: string;
  status: string;
  result?: FinSightResponse | null;
}

export interface ConversationDetail extends ConversationListItem {
  turns: ConversationTurn[];
}

export interface CanvasDetail {
  id: string;
  conversation_id: string;
  revision: number;
  response: FinSightResponse;
  created_at: string;
  updated_at: string;
}

export interface ResearchDetail extends ResearchListItem {
  result?: FinSightResponse | null;
}
