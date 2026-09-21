"use client";

import { useEffect, useState } from "react";

import { getMarketTicker } from "@/lib/api";
import type { MarketTickerItem } from "@/lib/types";


function formatPrice(item: MarketTickerItem) {
  if (item.price == null) return "—";
  return item.price.toLocaleString(undefined, {
    maximumFractionDigits: item.price >= 1_000 ? 0 : 2,
  });
}

export function MarketTicker({ onSelect }: { onSelect: (symbol: string) => void }) {
  const [items, setItems] = useState<MarketTickerItem[]>([]);

  useEffect(() => {
    let active = true;
    async function refresh() {
      try {
        const snapshot = await getMarketTicker();
        if (active) setItems(snapshot.items);
      } catch {
        // The research experience remains usable when the snapshot provider is unavailable.
      }
    }
    void refresh();
    const timer = window.setInterval(refresh, 5 * 60 * 1_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  if (!items.length) return <div className="market-ticker market-ticker-empty">Loading market snapshot…</div>;

  const tickerItems = [...items, ...items];
  return (
    <div className="market-ticker" aria-label="Delayed market snapshot">
      <div className="ticker-track">
        {tickerItems.map((item, index) => {
          const change = item.change_percent;
          const direction = change == null ? "neutral" : change >= 0 ? "positive" : "negative";
          return (
            <button
              className="ticker-item"
              key={`${item.symbol}-${index}`}
              onClick={() => onSelect(item.symbol)}
              aria-label={`Research ${item.name}`}
              tabIndex={index < items.length ? 0 : -1}
            >
              <strong>{item.symbol.replace("^", "")}</strong>
              <span>{formatPrice(item)}</span>
              <em className={direction}>{change == null ? "—" : `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`}</em>
            </button>
          );
        })}
      </div>
    </div>
  );
}
