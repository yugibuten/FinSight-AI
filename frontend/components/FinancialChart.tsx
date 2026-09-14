"use client";

import {
  Bar,
  BarChart,
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

import type { Chart } from "@/lib/types";


const COLORS = ["#126a4a", "#5571c8", "#c77932", "#8e5db7", "#168b91"];

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

export function FinancialChart({ chart }: { chart: Chart }) {
  const data = mergedData(chart);

  return (
    <section className="chart-card">
      <div className="section-title">
        <div><span className="section-kicker">Data visualization</span><h3>{chart.title}</h3></div>
        <span>{chart.unit ?? chart.y_axis}</span>
      </div>
      <div className="chart-canvas" role="img" aria-label={chart.title}>
        <ResponsiveContainer width="100%" height="100%">
          {chart.type === "bar" ? (
            <BarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid stroke="#e7ece8" vertical={false} />
              <XAxis dataKey="x" tick={{ fill: "#66756f", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#66756f", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => valueLabel(value, chart.unit)} />
              <Tooltip formatter={(value) => valueLabel(Number(value), chart.unit)} contentStyle={{ border: "1px solid #dce5df", borderRadius: 12, boxShadow: "0 12px 30px rgba(26,54,43,.1)" }} />
              <ReferenceLine y={0} stroke="#87938e" />
              {chart.series.map((series) => (
                <Bar key={series.name} dataKey={series.name} radius={[6, 6, 0, 0]}>
                  {series.data.map((point) => <Cell key={point.x} fill={point.y >= 0 ? "#126a4a" : "#b74646"} />)}
                </Bar>
              ))}
            </BarChart>
          ) : (
            <LineChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid stroke="#e7ece8" vertical={false} />
              <XAxis dataKey="x" minTickGap={42} tick={{ fill: "#66756f", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#66756f", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => valueLabel(value, chart.unit)} width={70} />
              <Tooltip formatter={(value) => valueLabel(Number(value), chart.unit)} contentStyle={{ border: "1px solid #dce5df", borderRadius: 12, boxShadow: "0 12px 30px rgba(26,54,43,.1)" }} />
              {chart.unit === "%" && <ReferenceLine y={0} stroke="#87938e" strokeDasharray="4 4" />}
              {chart.series.length > 1 && <Legend />}
              {chart.series.map((series, index) => (
                <Line key={series.name} type="monotone" dataKey={series.name} stroke={COLORS[index % COLORS.length]} strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} connectNulls />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
      <details className="chart-table">
        <summary>View chart data</summary>
        <div><table><thead><tr><th>{chart.x_axis}</th>{chart.series.map((series) => <th key={series.name}>{series.name}</th>)}</tr></thead><tbody>{data.map((row) => <tr key={String(row.x)}><td>{row.x}</td>{chart.series.map((series) => <td key={series.name}>{typeof row[series.name] === "number" ? valueLabel(Number(row[series.name]), chart.unit) : "—"}</td>)}</tr>)}</tbody></table></div>
      </details>
    </section>
  );
}
