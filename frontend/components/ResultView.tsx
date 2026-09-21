import { FinancialChart } from "@/components/FinancialChart";
import type { FinSightResponse, PresentationBlock, PresentationBlockType, PresentationPlan } from "@/lib/types";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

function changeClass(value?: string | null) {
  if (value?.trim().startsWith("+")) return "positive";
  if (value?.trim().startsWith("-")) return "negative";
  return "neutral";
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function SourceMarks({ ids }: { ids?: string[] }) {
  if (!ids?.length) return null;
  return <span className="source-marks" aria-label="Supporting sources">{ids.map((id) => <a href={`#source-${id}`} key={id}>[{id.replace("src_", "")}]</a>)}</span>;
}

function fallbackPresentation(result: FinSightResponse): PresentationPlan {
  const blocks: PresentationBlock[] = [];
  const add = (type: PresentationBlockType, data_ref: string, span: PresentationBlock["span"] = "full") =>
    blocks.push({ id: `${type}-${blocks.length}`, type, data_ref, span, variant: "default" });
  add("direct_answer", "direct_answer");
  if (result.headline) add("headline", "headline");
  result.charts.forEach((_, index) => add("chart", `charts.${index}`));
  if (result.metrics.length) add("metric_grid", "metrics");
  if (result.companies.length) add("company_grid", "companies");
  if (result.insights.length) add("insight_list", "insights", "half");
  if (result.evidence.length) add("evidence", "evidence", "half");
  if (result.news.length) add("news_feed", "news");
  add("summary", "summary");
  if (result.sources.length) add("source_list", "sources");
  return { layout: "explainer", blocks };
}

interface RenderActions { ask: (question: string) => void }
type BlockRenderer = (result: FinSightResponse, block: PresentationBlock, actions: RenderActions) => ReactNode;

function suggestedActions(result: FinSightResponse) {
  const suggestions: Record<string, string[]> = {
    stock_price: ["Show the 6-month performance chart", "Add financial metrics", "Show related news"],
    stock_history: ["Explain the biggest movement", "Show related news", "Highlight the main risks"],
    stock_comparison: ["Explain the performance difference", "Add valuation metrics", "Highlight the risks"],
    company_research: ["Add a price chart", "Show recent news", "Highlight the main risks"],
    financial_news: ["Explain the market impact", "Add the stock performance chart", "Show supporting metrics"],
    market_overview: ["Explain today's market direction", "Show the strongest sector", "Highlight market risks"],
    general_explanation: ["Give me an example", "Explain it more simply", "Show the key risks"],
  };
  return suggestions[result.response_type] ?? [];
}

const BLOCK_REGISTRY: Record<PresentationBlockType, BlockRenderer> = {
  direct_answer: (result, _block, actions) => (
    <section className="direct-answer-card">
      <div><span className="section-kicker">Direct answer</span><p>{result.direct_answer || result.summary} <SourceMarks ids={result.summary_source_ids} /></p></div>
      <div className="context-actions">{suggestedActions(result).map((label) => <button type="button" key={label} onClick={() => actions.ask(label)}>{label}<span>→</span></button>)}</div>
    </section>
  ),
  headline: (result) => result.headline && (
    <section className="headline-card">
      <div><span className="headline-label">{result.headline.label}</span><strong>{result.headline.value}</strong></div>
      {result.headline.change && <span className={`headline-change ${changeClass(result.headline.change)}`}>{result.headline.change}</span>}
      {result.headline.context && <p>{result.headline.context}</p>}
      <SourceMarks ids={result.headline.source_ids} />
    </section>
  ),
  headline_grid: (result) => Boolean(result.headlines?.length) && (
    <section className="headline-grid" aria-label="Stock prices">
      {result.headlines?.map((headline, index) => (
        <div className="headline-card headline-card-multi" key={`${headline.label}-${index}`}>
          <div><span className="headline-label">{headline.label}</span><strong>{headline.value}</strong></div>
          {headline.change && <span className={`headline-change ${changeClass(headline.change)}`}>{headline.change}</span>}
          {headline.context && <p>{headline.context}</p>}
          <SourceMarks ids={headline.source_ids} />
        </div>
      ))}
    </section>
  ),
  summary: (result) => <section className="summary-card"><span className="section-kicker">AI takeaway</span><p>{result.summary} <SourceMarks ids={result.summary_source_ids} /></p></section>,
  chart: (result, block, actions) => {
    const match = /^charts\.(\d+)$/.exec(block.data_ref);
    const chart = match ? result.charts[Number(match[1])] : undefined;
    return chart ? <FinancialChart chart={chart} onAction={actions.ask} /> : null;
  },
  metric_grid: (result, block) => result.metrics.length > 0 && (
    <section className="section-frame metric-section">
      <div className="section-title"><h3>{block.title ?? "Key metrics"}</h3><span>Supporting numbers</span></div>
      <div className="metric-grid">{result.metrics.map((metric, index) => (
        <details className="metric-card" key={`${metric.name}-${index}`}><summary><span>{metric.name}</span><strong>{metric.value}</strong>
          {metric.change && <em className={changeClass(metric.change)}>{metric.change}</em>}</summary>
          <div className="metric-detail"><small>{metric.context ?? "Supporting financial data used in this answer."}</small><SourceMarks ids={metric.source_ids} /></div>
        </details>
      ))}</div>
    </section>
  ),
  company_grid: (result, block) => result.companies.length > 0 && (
    <section className="section-frame company-section">
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
      <ul className="insight-list">{result.insights.map((item, index) => <li key={index}>{item} <SourceMarks ids={result.insight_citations?.find((citation) => citation.text === item)?.source_ids} /></li>)}</ul>
    </section>
  ),
  evidence: (result, block) => result.evidence.length > 0 && (
    <section className="panel evidence-panel"><div className="section-title"><h3>{block.title ?? "Supporting evidence"}</h3></div>
      {result.evidence.map((item, index) => <details className="evidence-row" key={`${item.metric}-${index}`}>
        <summary><span>{item.metric}</span><strong>{item.value}</strong></summary><p><b>{item.claim}</b>{item.explanation ? ` — ${item.explanation}` : ""} <SourceMarks ids={item.source_ids} /></p>
      </details>)}
    </section>
  ),
  news_feed: (result, block) => result.news.length > 0 && (
    <section className="section-frame news-section"><div className="section-title"><h3>{block.title ?? "Related news"}</h3><span>{result.news.length} stories</span></div>
      <div className="news-list">{result.news.map((item, index) => (
        <a className="news-card" key={`${item.title}-${index}`} href={item.url ?? "#"} target="_blank" rel="noreferrer">
          <div><span>{item.publisher ?? "Financial news"}</span>{item.published_at && <time>{formatDate(item.published_at)}</time>}</div>
          <h4>{item.title} <SourceMarks ids={item.source_ids} /></h4>{item.summary && <p>{item.summary}</p>}<b>Read source ↗</b>
        </a>
      ))}</div>
    </section>
  ),
  source_list: (result, block) => result.sources.length > 0 && (
    <section className="sources section-frame"><div className="section-title"><h3>{block.title ?? "Sources"}</h3><span>Evidence trail</span></div>
      {result.sources.map((source) => <a id={source.id ? `source-${source.id}` : undefined} key={source.url} href={source.url} target="_blank" rel="noreferrer"><span>{source.id ? `[${source.id.replace("src_", "")}] ${source.provider}` : source.provider}</span><b>{source.title}</b><em>↗</em></a>)}
    </section>
  ),
  // Tool calls remain in the API response for evaluation, but are intentionally
  // hidden from the customer-facing research page.
  tool_activity: () => null,
};

const BLOCK_LABELS: Partial<Record<PresentationBlockType, string>> = {
  direct_answer: "answer", headline: "price", headline_grid: "prices", summary: "summary",
  chart: "chart", metric_grid: "metrics", company_grid: "companies", insight_list: "insights",
  evidence: "evidence", news_feed: "news", source_list: "sources",
};

export function ResultView({ result, onFollowUp }: { result: FinSightResponse; onFollowUp: (question: string) => void }) {
  const presentation = useMemo(() => result.presentation ?? fallbackPresentation(result), [result]);
  const [blocks, setBlocks] = useState(presentation.blocks);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setBlocks((current) => {
      const incoming = presentation.blocks;
      const retained = current.filter((block) => incoming.some((item) => item.id === block.id));
      const added = incoming.filter((block) => !retained.some((item) => item.id === block.id));
      return [...retained, ...added];
    });
  }, [presentation.blocks]);

  useEffect(() => {
    if (!expanded) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpanded(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [expanded]);

  function move(index: number, direction: -1 | 1) {
    setBlocks((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function download(block: PresentationBlock) {
    const field = block.data_ref.split(".")[0] as keyof FinSightResponse;
    const payload = JSON.stringify({ query: result.query, section: block.type, data: result[field] }, null, 2);
    const url = URL.createObjectURL(new Blob([payload], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `finsight-${block.type}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const currencies = [...new Set(result.companies.map((company) => company.currency).filter(Boolean))];
  return (
    <article className="result" aria-live="polite">
      <header className="result-header">
        <div><span className="eyebrow">Generated financial research</span><h2>{result.title}</h2><p className="result-query">{result.query}</p></div>
        <div className="result-meta"><span className="result-type">{result.response_type.replaceAll("_", " ")}</span><div className="market-context"><span>Latest available session</span><span>May be delayed</span>{currencies.map((currency) => <span key={currency}>{currency}</span>)}</div><span className="freshness">Updated {formatDate(result.generated_at)}</span></div>
      </header>
      <div className={`dynamic-layout layout-${presentation.layout}`}>
        {blocks.map((block, index) => {
          const renderer = BLOCK_REGISTRY[block.type];
          const updated = result.canvas_operations?.some((operation) => operation.block_type === block.type);
          const label = BLOCK_LABELS[block.type] ?? block.type;
          return renderer ? <div className={`dynamic-block block-${block.type} span-${block.span} variant-${block.variant}${updated ? " canvas-block-updated" : ""}${expanded === block.id ? " block-expanded" : ""}`} key={block.id}>
            <div className="block-controls" aria-label={`${label} controls`}>
              <button type="button" title="Move up" disabled={index === 0} onClick={() => move(index, -1)}>↑</button>
              <button type="button" title="Move down" disabled={index === blocks.length - 1} onClick={() => move(index, 1)}>↓</button>
              <button type="button" title={expanded === block.id ? "Exit fullscreen" : "Open fullscreen"} aria-label={expanded === block.id ? "Exit fullscreen" : `Open ${label} fullscreen`} onClick={() => setExpanded(expanded === block.id ? null : block.id)}>{expanded === block.id ? "↙" : "⤢"}</button>
              <button type="button" title="Refresh" onClick={() => onFollowUp(`Refresh the ${label}`)}>↻</button>
              <button type="button" title="Download" onClick={() => download(block)}>⇩</button>
              <button type="button" title="Remove" onClick={() => onFollowUp(`Remove the ${label} from the screen`)}>×</button>
            </div>
            {renderer(result, block, { ask: onFollowUp })}
          </div> : null;
        })}
      </div>
    </article>
  );
}
