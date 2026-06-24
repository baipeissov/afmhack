export function PageIntro({
  title,
  lead,
  right,
}: {
  title: string;
  lead: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border-subtle pb-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-text-primary">
          {title}
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-text-secondary">{lead}</p>
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}
