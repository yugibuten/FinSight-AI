"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect, useState } from "react";

import type { Chart } from "@/lib/types";


const COLORS = ["#3ddc84", "#76a9ff", "#f6bd60", "#b794f6", "#38bfc3"];
type ChartView = "line" | "area" | "bar";
const CHART_VIEWS: ChartView[] = ["line", "area", "bar"];
type ChartRange = "1W" | "1M" | "3M" | "6M" | "1Y" | "ALL";
const RANGE_DAYS: Record<ChartRange, number | null> = { "1W": 7, "1M": 31, "3M": 93, "6M": 186, "1Y": 366, ALL: null };

function mergedData(chart: Chart) {
  const rows = new Map<string, Record<string, string | number>>();
  for (const series of chart.series) {
    for (const point of series.data) {
      const row = rows.get(point.x) ?? { x: point.x };
      row[series.name] = point.y;
      rows.set(point.x, row);
    }
  }
  return Array.from(rows.values());
}

function valueLabel(value: number, unit?: string | null) {
  if (unit === "%") return `${value.toFixed(2)}%`;
  return `${unit && unit !== "Unknown" ? `${unit} ` : ""}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export function FinancialChart({ chart, onAction }: { chart: Chart; onAction?: (question: string) => void }) {
  const rawData = mergedData(chart);
  const [view, setView] = useState<ChartView>(chart.type);
  const [range, setRange] = useState<ChartRange>("ALL");
  const [percentage, setPercentage] = useState(chart.unit === "%");
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareTicker, setCompareTicker] = useState("");
  const gradientPrefix = `chart-${chart.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  const latestDate = new Date(String(rawData.at(-1)?.x ?? ""));
  let data = rawData;
  const days = RANGE_DAYS[range];
  if (days && !Number.isNaN(latestDate.getTime())) {
    const cutoff = new Date(latestDate);
    cutoff.setDate(cutoff.getDate() - days);
    data = rawData.filter((row) => new Date(String(row.x)) >= cutoff);
  }
  if (percentage && data.length) {
    const starts = Object.fromEntries(chart.series.map((series) => [series.name, Number(data[0][series.name])]));
    data = data.map((row) => ({
      ...row,
      ...Object.fromEntries(chart.series.map((series) => {
        const start = starts[series.name];
        const value = Number(row[series.name]);
        return [series.name, start && Number.isFinite(value) ? ((value - start) / start) * 100 : value];
      })),
    }));
  }
  const displayUnit = percentage ? "%" : chart.unit;

  useEffect(() => {
    setView(chart.type);
    setRange("ALL");
    setPercentage(chart.unit === "%");
  }, [chart.id, chart.type, chart.unit]);

  function downloadCsv() {
    const headings = [chart.x_axis, ...chart.series.map((series) => series.name)];
    const rows = data.map((row) => [row.x, ...chart.series.map((series) => row[series.name] ?? "")]);
    const csv = [headings, ...rows].map((row) => row.map((value) => JSON.stringify(value)).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${chart.id}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function compare() {
    const ticker = compareTicker.trim().toUpperCase();
    if (!ticker || !onAction) return;
    onAction(`Compare ${chart.series.map((series) => series.name).join(" and ")} with ${ticker} over the same period`);
    setCompareTicker("");
    setCompareOpen(false);
  }

  return (
    <section className="chart-card">
      <div className="section-title">
        <div><span className="section-kicker">Data visualization</span><h3>{chart.title}</h3></div>
        <div className="chart-options">
          <span>{chart.unit ?? chart.y_axis}</span>
          <div className="chart-view-toggle" aria-label="Chart type">
            {CHART_VIEWS.map((option) => (
              <button key={option} type="button" className={view === option ? "active" : ""} aria-pressed={view === option} onClick={() => setView(option)}>
                {option[0].toUpperCase() + option.slice(1)}
              </button>
            ))}
          </div>
          <select className="chart-view-select" aria-label="Chart type" value={view} onChange={(event) => setView(event.target.value as ChartView)}>
            {CHART_VIEWS.map((option) => <option key={option} value={option}>{option[0].toUpperCase() + option.slice(1)}</option>)}
          </select>
        </div>
      </div>
      <div className="chart-toolbar">
        <div className="chart-ranges">{(Object.keys(RANGE_DAYS) as ChartRange[]).map((option) => <button type="button" className={range === option ? "active" : ""} key={option} onClick={() => setRange(option)}>{option}</button>)}</div>
        <div className="chart-actions">
          <button type="button" className={percentage ? "active" : ""} onClick={() => setPercentage((value) => !value)}>% return</button>
          <button type="button" onClick={() => setCompareOpen((value) => !value)}>＋ Compare</button>
          <button type="button" onClick={downloadCsv}>↓ CSV</button>
        </div>
      </div>
      {compareOpen && <form className="chart-compare" onSubmit={(event) => { event.preventDefault(); compare(); }}><input value={compareTicker} onChange={(event) => setCompareTicker(event.target.value)} placeholder="Ticker, e.g. MSFT" aria-label="Ticker to compare" /><button type="submit">Add comparison</button></form>}
      <div className="chart-canvas" role="img" aria-label={chart.title}>
        <ResponsiveContainer width="100%" height="100%">
          {view === "bar" ? (
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid stroke="#203129" vertical={false} />
              <XAxis dataKey="x" tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => valueLabel(value, displayUnit)} />
              <Tooltip cursor={{ fill: "rgba(61,220,132,.05)" }} formatter={(value) => valueLabel(Number(value), displayUnit)} contentStyle={{ color: "#eef5f1", background: "#101b16", border: "1px solid #2a4035", borderRadius: 12, boxShadow: "0 18px 45px rgba(0,0,0,.3)" }} />
              <ReferenceLine y={0} stroke="#52635b" />
              {chart.series.map((series) => (
                <Bar key={series.name} dataKey={series.name} radius={[6, 6, 0, 0]}>
                  {series.data.map((point) => <Cell key={point.x} fill={point.y >= 0 ? "#3ddc84" : "#ff7185"} />)}
                </Bar>
              ))}
              {data.length > 14 && <Brush dataKey="x" height={18} stroke="#3d7455" fill="#0a1510" travellerWidth={6} />}
            </BarChart>
          ) : view === "area" ? (
            <AreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 4 }}>
              <defs>
                {chart.series.map((series, index) => (
                  <linearGradient key={series.name} id={`${gradientPrefix}-${index}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.015} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid stroke="#203129" vertical={false} />
              <XAxis dataKey="x" minTickGap={42} tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => valueLabel(value, displayUnit)} width={70} />
              <Tooltip cursor={{ stroke: "#3d7455", strokeDasharray: "4 4" }} formatter={(value) => valueLabel(Number(value), displayUnit)} contentStyle={{ color: "#eef5f1", background: "#101b16", border: "1px solid #2a4035", borderRadius: 12, boxShadow: "0 18px 45px rgba(0,0,0,.3)" }} />
              {displayUnit === "%" && <ReferenceLine y={0} stroke="#52635b" strokeDasharray="4 4" />}
              {chart.series.length > 1 && <Legend />}
              {chart.series.map((series, index) => (
                <Area key={series.name} type="monotone" dataKey={series.name} stroke={COLORS[index % COLORS.length]} strokeWidth={2.5} fill={`url(#${gradientPrefix}-${index})`} activeDot={{ r: 5 }} connectNulls />
              ))}
              {data.length > 14 && <Brush dataKey="x" height={18} stroke="#3d7455" fill="#0a1510" travellerWidth={6} />}
            </AreaChart>
          ) : (
            <LineChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid stroke="#203129" vertical={false} />
              <XAxis dataKey="x" minTickGap={42} tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#84958d", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => valueLabel(value, displayUnit)} width={70} />
              <Tooltip cursor={{ stroke: "#3d7455", strokeDasharray: "4 4" }} formatter={(value) => valueLabel(Number(value), displayUnit)} contentStyle={{ color: "#eef5f1", background: "#101b16", border: "1px solid #2a4035", borderRadius: 12, boxShadow: "0 18px 45px rgba(0,0,0,.3)" }} />
              {displayUnit === "%" && <ReferenceLine y={0} stroke="#52635b" strokeDasharray="4 4" />}
              {chart.series.length > 1 && <Legend />}
              {chart.series.map((series, index) => (
                <Line key={series.name} type="monotone" dataKey={series.name} stroke={COLORS[index % COLORS.length]} strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} connectNulls />
              ))}
              {data.length > 14 && <Brush dataKey="x" height={18} stroke="#3d7455" fill="#0a1510" travellerWidth={6} />}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
      <details className="chart-table">
        <summary>View chart data</summary>
        <div><table><thead><tr><th>{chart.x_axis}</th>{chart.series.map((series) => <th key={series.name}>{series.name}</th>)}</tr></thead><tbody>{data.map((row) => <tr key={String(row.x)}><td>{row.x}</td>{chart.series.map((series) => <td key={series.name}>{typeof row[series.name] === "number" ? valueLabel(Number(row[series.name]), displayUnit) : "—"}</td>)}</tr>)}</tbody></table></div>
      </details>
    </section>
  );
}
