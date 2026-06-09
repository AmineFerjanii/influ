interface HashtagMentionPanelProps {
  title: string
  items: { label: string; count: number }[]
}

export function HashtagMentionPanel({ title, items }: HashtagMentionPanelProps) {
  const max = items[0]?.count ?? 1

  return (
    <div className="bg-ealan-bg border border-ealan-border rounded-xl p-4">
      <h4 className="section-label mb-3">{title}</h4>
      {items.length === 0 ? (
        <p className="text-xs text-ealan-muted">No data available</p>
      ) : (
        <ul className="space-y-2">
          {items.map(({ label, count }) => (
            <li key={label} className="flex items-center gap-2">
              <span className="text-xs text-gray-300 w-28 truncate shrink-0">{label}</span>
              <div className="flex-1 bg-ealan-hover rounded-full h-1 overflow-hidden">
                <div
                  className="bg-brand-500 h-full rounded-full opacity-70"
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
              <span className="text-[11px] text-ealan-muted w-5 text-right shrink-0">{count}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
