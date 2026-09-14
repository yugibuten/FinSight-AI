import { FinancialChart } from "@/components/FinancialChart";
import type { FinSightResponse, PresentationBlock, PresentationBlockType, PresentationPlan } from "@/lib/types";
import type { ReactNode } from "react";

function changeClass(value?: string | null) {
  if (value?.trim().startsWith("+")) return "positive";
  if (value?.trim().startsWith("-")) return "negative";
  return "neutral";
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function fallbackPresentation(result: FinSightResponse): PresentationPlan {
  const blocks: PresentationBlock[] = [];
  const add = (type: PresentationBlockType, data_ref: string, span: PresentationBlock["span"] = "full") =>
    blocks.push({ id: `${type}-${blocks.length}`, type, data_ref, span, variant: "default" });
  if (result.headline) add("headline", "headline");
  add("summary", "summary");
  result.charts.forEach((_, index) => add("chart", `charts.${index}`));
  if (result.metrics.length) add("metric_grid", "metrics");
  if (result.companies.length) add("company_grid", "companies");
  if (result.insights.length) add("insight_list", "insights", "half");
  if (result.evidence.length) add("evidence", "evidence", "half");
  if (result.news.length) add("news_feed", "news");
  if (result.sources.length) add("source_list", "sources");
  if (result.tool_calls.length) add("tool_activity", "tool_calls");
  return { layout: "explainer", blocks };
}

type BlockRenderer = (result: FinSightResponse, block: PresentationBlock) => ReactNode;

const BLOCK_REGISTRY: Record<PresentationBlockType, BlockRenderer> = {
  headline: (result) => result.headline && (
    <section className="headline-card">
      <div><span className="headline-label">{result.headline.label}</span><strong>{result.headline.value}</strong></div>
      {result.headline.change && <span className={`headline-change ${changeClass(result.headline.change)}`}>{result.headline.change}</span>}
      {result.headline.context && <p>{result.headline.context}</p>}
    </section>
  ),
  summary: (result) => <section className="summary-card"><span className="section-kicker">AI summary</span><p>{result.summary}</p></section>,
  chart: (result, block) => {
    const match = /^charts\.(\d+)$/.exec(block.data_ref);
    const chart = match ? result.charts[Number(match[1])] : undefined;
    return chart ? <FinancialChart chart={chart} /> : null;
  },
  metric_grid: (result, block) => result.metrics.length > 0 && (
    <section>
      <div className="section-title"><h3>{block.title ?? "Key metrics"}</h3><span>Supporting numbers</span></div>
      <div className="metric-grid">{result.metrics.map((metric, index) => (
        <div className="metric-card" key={`${metric.name}-${index}`}><span>{metric.name}</span><strong>{metric.value}</strong>
          {metric.change && <em className={changeClass(metric.change)}>{metric.change}</em>}
          {metric.context && <small>{metric.context}</small>}
        </div>
      ))}</div>
    </section>
  ),
  company_grid: (result, block) => result.companies.length > 0 && (
    <section>
      <div className="section-title"><h3>{block.title ?? "Companies"}</h3><span>At a glance</span></div>
      <div className="company-grid">{result.companies.map((company) => (
        <div className="company-card" key={company.ticker}>
          <div><b>{company.name ?? company.ticker}</b><span>{company.ticker}</span></div>
          {company.price && <strong>{company.price} {company.currency}</strong>}
          {company.change && <em className={changeClass(company.change)}>{company.change}</em>}
          {(company.sector || company.industry) && <p>{[company.sector, company.industry].filter(Boolean).join(" · ")}</p>}
        </div>
      ))}</div>
    </section>
  ),
  insight_list: (result, block) => result.insights.length > 0 && (
    <section className="panel"><div className="section-title"><h3>{block.title ?? "Insights"}</h3></div>
      <ul className="insight-list">{result.insights.map((item, index) => <li key={index}>{item}</li>)}</ul>
    </section>
  ),
  evidence: (result, block) => result.evidence.length > 0 && (
    <section className="panel evidence-panel"><div className="section-title"><h3>{block.title ?? "Supporting evidence"}</h3></div>
      {result.evidence.map((item, index) => <div className="evidence-row" key={`${item.metric}-${index}`}>
        <div><span>{item.metric}</span><strong>{item.value}</strong></div><p><b>{item.claim}</b>{item.explanation ? ` — ${item.explanation}` : ""}</p>
      </div>)}
    </section>
  ),
  news_feed: (result, block) => result.news.length > 0 && (
    <section><div className="section-title"><h3>{block.title ?? "Related news"}</h3><span>{result.news.length} stories</span></div>
      <div className="news-list">{result.news.map((item, index) => (
        <a className="news-card" key={`${item.title}-${index}`} href={item.url ?? "#"} target="_blank" rel="noreferrer">
          <div><span>{item.publisher ?? "Financial news"}</span>{item.published_at && <time>{formatDate(item.published_at)}</time>}</div>
          <h4>{item.title}</h4>{item.summary && <p>{item.summary}</p>}<b>Read source ↗</b>
        </a>
      ))}</div>
    </section>
  ),
  source_list: (result, block) => result.sources.length > 0 && (
    <section className="sources"><div className="section-title"><h3>{block.title ?? "Sources"}</h3><span>Evidence trail</span></div>
      {result.sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer"><span>{source.provider}</span><b>{source.title}</b><em>↗</em></a>)}
    </section>
  ),
  tool_activity: (result) => result.tool_calls.length > 0 && (
    <details className="debug-panel"><summary>Tool activity <span>{result.tool_calls.length}</span></summary><pre>{JSON.stringify(result.tool_calls, null, 2)}</pre></details>
  ),
};

export function ResultView({ result }: { result: FinSightResponse }) {
  const presentation = result.presentation ?? fallbackPresentation(result);
  return (
    <article className="result" aria-live="polite">
      <header className="result-header">
        <div><span className="eyebrow">{result.response_type.replaceAll("_", " ")}</span><h2>{result.title}</h2></div>
        <span className="freshness">Updated {formatDate(result.generated_at)}</span>
      </header>
      <div className={`dynamic-layout layout-${presentation.layout}`}>
        {presentation.blocks.map((block) => {
          const renderer = BLOCK_REGISTRY[block.type];
          return renderer ? <div className={`dynamic-block span-${block.span} variant-${block.variant}`} key={block.id}>{renderer(result, block)}</div> : null;
        })}
      </div>
    </article>
  );
}
