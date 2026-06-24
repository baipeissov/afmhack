"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { riskInflow } from "@/mocks/dashboard";

export function RiskInflowArea() {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={riskInflow} margin={{ top: 8, right: 4, left: -20, bottom: 0 }}>
        <defs>
          {(["critical", "high", "medium"] as const).map((k) => (
            <linearGradient key={k} id={`g-${k}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={`var(--sev-${k})`} stopOpacity={0.5} />
              <stop offset="100%" stopColor={`var(--sev-${k})`} stopOpacity={0.02} />
            </linearGradient>
          ))}
        </defs>
        <XAxis
          dataKey="t"
          tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "var(--font-mono)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--border-subtle)" }}
          tickFormatter={(v) => `-${72 - v * 3}h`}
          interval={5}
        />
        <YAxis
          tick={{ fill: "var(--text-muted)", fontSize: 10, fontFamily: "var(--font-mono)" }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip
          contentStyle={{
            background: "var(--bg-surface-2)",
            border: "1px solid var(--border-strong)",
            borderRadius: 8,
            fontSize: 12,
            fontFamily: "var(--font-mono)",
          }}
          labelStyle={{ color: "var(--text-muted)" }}
        />
        <Area type="monotone" dataKey="medium" stackId="1" stroke="var(--sev-medium)" fill="url(#g-medium)" strokeWidth={1.5} />
        <Area type="monotone" dataKey="high" stackId="1" stroke="var(--sev-high)" fill="url(#g-high)" strokeWidth={1.5} />
        <Area type="monotone" dataKey="critical" stackId="1" stroke="var(--sev-critical)" fill="url(#g-critical)" strokeWidth={1.5} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
