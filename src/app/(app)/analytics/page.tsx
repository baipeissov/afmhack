import { Card, CardHeader, CardTitle, CardBody } from "@/components/ui/card";

const techniques = [
  { label: "Urgency", n: 312, max: 312 },
  { label: "False authority", n: 244, max: 312 },
  { label: "Recruit-to-earn", n: 198, max: 312 },
  { label: "Guaranteed ROI", n: 141, max: 312 },
  { label: "Sunk cost", n: 97, max: 312 },
];

const efficacy = [
  { persona: "Due-diligence", win: 81, msgs: 9, contra: 4.4, best: true },
  { persona: "Skeptic", win: 74, msgs: 11, contra: 3.1, best: false },
  { persona: "Eager novice", win: 52, msgs: 14, contra: 1.2, best: false },
];

const cohorts = [
  { platform: "TikTok", cases: 141, conf: 0.88, delta: "▲" },
  { platform: "Instagram", cases: 96, conf: 0.82, delta: "▲" },
  { platform: "YouTube", cases: 40, conf: 0.79, delta: "▬" },
];

export default function Analytics() {
  const exposure = 72;
  return (
    <div className="space-y-4 p-5">
      <h1 className="text-lg font-semibold tracking-tight">Risk Analytics</h1>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Exposure index</CardTitle>
          </CardHeader>
          <CardBody className="flex flex-col items-center">
            <div className="relative grid size-32 place-items-center">
              <svg viewBox="0 0 100 100" className="absolute size-full -rotate-90">
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--bg-surface-3)" strokeWidth="8" />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="var(--sev-high)"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${(exposure / 100) * 264} 264`}
                />
              </svg>
              <div className="text-center">
                <div className="font-mono text-3xl font-medium text-text-primary">{exposure}</div>
                <div className="text-[10px] uppercase tracking-wide text-sev-high">Elevated ▲</div>
              </div>
            </div>
            <p className="mt-2 text-center text-xs text-text-muted">blended org risk score</p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Manipulation techniques · frequency</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            {techniques.map((t) => (
              <div key={t.label}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-text-secondary">{t.label}</span>
                  <span className="font-mono tabular-nums text-text-muted">{t.n}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-bg-surface-3">
                  <div
                    className="h-full rounded-full bg-manipulation"
                    style={{ width: `${(t.n / t.max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Agent efficacy</CardTitle>
          </CardHeader>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[10px] uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2 font-medium">Persona</th>
                <th className="px-4 py-2 font-medium">Win%</th>
                <th className="px-4 py-2 font-medium">Avg msgs</th>
                <th className="px-4 py-2 font-medium">Contra/case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {efficacy.map((e) => (
                <tr key={e.persona}>
                  <td className="px-4 py-2.5 text-text-primary">
                    {e.persona} {e.best && <span className="text-sev-medium">★</span>}
                  </td>
                  <td className="px-4 py-2.5 font-mono tabular-nums text-text-secondary">{e.win}</td>
                  <td className="px-4 py-2.5 font-mono tabular-nums text-text-secondary">{e.msgs}</td>
                  <td className="px-4 py-2.5 font-mono tabular-nums text-text-secondary">{e.contra}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cohorts / hotspots</CardTitle>
          </CardHeader>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[10px] uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2 font-medium">Platform</th>
                <th className="px-4 py-2 font-medium">Cases</th>
                <th className="px-4 py-2 font-medium">Conf</th>
                <th className="px-4 py-2 font-medium">Δ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {cohorts.map((c) => (
                <tr key={c.platform}>
                  <td className="px-4 py-2.5 text-text-primary">{c.platform}</td>
                  <td className="px-4 py-2.5 font-mono tabular-nums text-text-secondary">{c.cases}</td>
                  <td className="px-4 py-2.5 font-mono tabular-nums text-text-secondary">
                    {c.conf.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5 text-sev-high">{c.delta}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border-subtle px-4 py-2.5 font-mono text-[11px] text-text-muted">
            geo: EU-W 38% · MENA 21% · SEA 18%
          </div>
        </Card>
      </div>
    </div>
  );
}
