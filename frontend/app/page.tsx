"use client";

import { useCallback, useEffect, useState } from "react";
import { QueryForm } from "@/components/QueryForm";
import { ResearchHistory } from "@/components/ResearchHistory";
import { ResultView } from "@/components/ResultView";
import { askFinSight, deleteSavedResearch, getResearchHistory, getSavedResearch } from "@/lib/api";
import type { FinSightResponse, ResearchListItem } from "@/lib/types";

export default function Home() {
  const [result, setResult] = useState<FinSightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeQuestion, setActiveQuestion] = useState("");
  const [history, setHistory] = useState<ResearchListItem[]>([]);
  const [historyBusyId, setHistoryBusyId] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await getResearchHistory());
    } catch {
      // The main query experience remains usable if history is unavailable.
    }
  }, []);

  useEffect(() => { void refreshHistory(); }, [refreshHistory]);

  async function ask(question: string) {
    setActiveQuestion(question);
    setLoading(true);
    setError(null);
    try {
      setResult(await askFinSight(question));
      await refreshHistory();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function openResearch(id: string) {
    setHistoryBusyId(id);
    setError(null);
    try {
      const saved = await getSavedResearch(id);
      if (saved.result) {
        setResult(saved.result);
        setActiveQuestion(saved.result.query);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not open saved research");
    } finally {
      setHistoryBusyId(null);
    }
  }

  async function removeResearch(id: string) {
    setHistoryBusyId(id);
    try {
      await deleteSavedResearch(id);
      setHistory((items) => items.filter((item) => item.id !== id));
      if (result?.research_id === id) setResult(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not delete saved research");
    } finally {
      setHistoryBusyId(null);
    }
  }

  return (
    <main className="app-shell">
      <nav className="topbar">
        <a className="brand" href="#"><span>F</span> FinSight</a>
        <div className="status"><i /> FinSight V3</div>
      </nav>

      <div className="conversation">
        {!result && !loading && (
          <section className="welcome">
            <div className="welcome-mark">F</div>
            <span className="hero-kicker">Grounded financial intelligence</span>
            <h1>What can I help you <em>understand?</em></h1>
            <p>Research a stock, compare companies, follow market movements, or unpack a financial story.</p>
          </section>
        )}

        {!loading && !result && <ResearchHistory items={history} busyId={historyBusyId} onOpen={openResearch} onDelete={removeResearch} />}
        {(result || loading) && <div className="user-message"><span>You</span><p>{activeQuestion || result?.query}</p></div>}
        {loading && <section className="loading-card" aria-live="polite">
          <div className="loader"><i /><i /><i /></div>
          <div><strong>Building your research brief</strong><span>Finding data, checking evidence, and preparing the answer…</span></div>
        </section>}
        {error && <div className="error-card"><b>We couldn’t complete that research.</b><span>{error}</span></div>}
        {result && !loading && <ResultView result={result} />}
        <footer>FinSight uses market data for research and education. It is not financial advice.</footer>
      </div>

      <div className="composer-dock">
        <QueryForm loading={loading} onSubmit={ask} showExamples={!result && !loading} />
        <small>FinSight can make mistakes. Verify important financial information.</small>
      </div>
    </main>
  );
}
