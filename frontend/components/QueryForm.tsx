"use client";

import { FormEvent, useState } from "react";

const EXAMPLES = [
  "What is Apple's latest stock price?",
  "Compare Apple and Microsoft over one year.",
  "Why is Tesla moving today?",
  "How are Indian markets performing today?",
];

interface QueryFormProps {
  loading: boolean;
  onSubmit: (question: string) => void;
  showExamples?: boolean;
}

export function QueryForm({ loading, onSubmit, showExamples = false }: QueryFormProps) {
  const [question, setQuestion] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = question.trim();
    if (value && !loading) {
      onSubmit(value);
      setQuestion("");
    }
  }

  return (
    <div className="query-wrap">
      <form className="query-form" onSubmit={submit}>
        <input
          aria-label="Ask FinSight a financial question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about a stock, company, market, or financial story…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()} aria-label="Send question">
          {loading ? <span className="send-loader" /> : <span aria-hidden="true">↑</span>}
        </button>
      </form>
      {showExamples && <div className="examples" aria-label="Example questions">
        {EXAMPLES.map((example) => (
          <button key={example} onClick={() => onSubmit(example)} disabled={loading}>
            {example}
          </button>
        ))}
      </div>}
    </div>
  );
}
