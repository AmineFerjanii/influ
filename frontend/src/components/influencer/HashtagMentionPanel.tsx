interface HashtagMentionPanelProps {
  title: string
  items: { label: string; count: number }[]
}

export function HashtagMentionPanel({ title, items }: HashtagMentionPanelProps) {
  const max = items[0]?.count ?? 1

  return (
    <div className="bg-gray-800/50 rounded-xl p-4">
      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">{title}</h4>
      {items.length === 0 ? (
        <p className="text-xs text-gray-600">No data available</p>
      ) : (
        <ul className="space-y-2">
          {items.map(({ label, count }) => (
            <li key={label} className="flex items-center gap-2">
              <span className="text-xs text-gray-300 w-28 truncate shrink-0">{label}</span>
              <div className="flex-1 bg-gray-700 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full"
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-5 text-right shrink-0">{count}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
