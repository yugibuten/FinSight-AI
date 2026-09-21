"use client";

import { useRef, useState } from "react";
import { QueryForm } from "@/components/QueryForm";
import { MarketTicker } from "@/components/MarketTicker";
import { ResultView } from "@/components/ResultView";
import { streamFinSight } from "@/lib/api";
import type { FinSightResponse, PresentationBlock } from "@/lib/types";

export default function Home() {
  const [result, setResult] = useState<FinSightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeQuestion, setActiveQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const streamController = useRef<AbortController | null>(null);

  async function ask(question: string) {
    if (loading) return;
    setActiveQuestion(question);
    setLoading(true);
    setError(null);
    const controller = new AbortController();
    streamController.current = controller;
    try {
      await streamFinSight(
        question,
        conversationId,
        result?.canvas_revision,
        (event, data) => {
          if (event === "response_start") {
            const response = data.response as FinSightResponse;
            setResult(response);
            setConversationId(response.conversation_id ?? null);
          } else if (event === "component") {
            const block = data.block as PresentationBlock;
            setResult((current) => current ? {
              ...current,
              presentation: {
                layout: current.presentation?.layout ?? "explainer",
                blocks: [...(current.presentation?.blocks ?? []), block],
              },
            } : current);
          }
        },
        controller.signal,
      );
    } catch (cause) {
      if (!(cause instanceof DOMException && cause.name === "AbortError")) {
        setError(cause instanceof Error ? cause.message : "Something went wrong");
      }
    } finally {
      if (streamController.current === controller) streamController.current = null;
      setLoading(false);
    }
  }

  function startNewResearch() {
    streamController.current?.abort();
    streamController.current = null;
    setResult(null);
    setError(null);
    setActiveQuestion("");
    setConversationId(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <main className="app-shell">
      <nav className="topbar">
        <button className="brand brand-button" onClick={startNewResearch}><span>F</span> FinSight</button>
        <MarketTicker onSelect={(symbol) => {
          if (!loading) void ask(`Show me the latest price for ${symbol}`);
        }} />
        <div className="nav-actions">
          {conversationId && <button className="new-research" onClick={startNewResearch}>＋ New research</button>}
          <div className="status" title="Quotes may be delayed"><i /> Market snapshot</div>
        </div>
      </nav>

      <div className="conversation">
        {!result && !loading && (
          <section className="welcome">
            <h1>Welcome to FinSight</h1>
            <p className="welcome-promise"><span>Markets.</span> <span>Explained.</span> <em>Clearly.</em></p>
          </section>
        )}
        {loading && <section className={`loading-card ${result ? "canvas-loading" : ""}`} aria-live="polite">
          <div className="loader"><i /><i /><i /></div>
          <div className="loading-copy"><span>{activeQuestion}</span></div>
        </section>}
        {loading && !result && <div className="research-skeleton" aria-hidden="true">
          <div className="skeleton-price"><i /><i /><i /></div>
          <div className="skeleton-summary"><i /><i /><i /></div>
          <div className="skeleton-grid"><div><i /><i /></div><div><i /><i /></div><div><i /><i /></div></div>
        </div>}
        {error && <div className="error-card"><b>We couldn’t complete that research.</b><span>{error}</span></div>}
        {result && <ResultView key={`${result.research_id}-${result.canvas_revision ?? 0}`} result={result} onFollowUp={ask} />}
        <footer>FinSight uses market data for research and education. It is not financial advice.</footer>
      </div>

      <div className="composer-dock">
        <QueryForm loading={loading} onSubmit={ask} />
        <small>FinSight can make mistakes. Verify important financial information.</small>
      </div>
    </main>
  );
}
