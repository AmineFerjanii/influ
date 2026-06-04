const CDN_DOMAINS = ['fbcdn.net', 'cdninstagram.com', 'tiktokcdn.com', 'p16-', 'p19-']

export function proxyImage(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  const needsProxy = CDN_DOMAINS.some((d) => url.includes(d))
  if (!needsProxy) return url
  return `/api/proxy-image?url=${encodeURIComponent(url)}`
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toLocaleString()
}

export function formatEngagementRate(er: number): string {
  return `${er.toFixed(2)}%`
}

export function erColor(er: number): string {
  if (er >= 6) return 'text-blue-400 bg-blue-400/10'
  if (er >= 3) return 'text-green-400 bg-green-400/10'
  if (er >= 1) return 'text-yellow-400 bg-yellow-400/10'
  return 'text-gray-400 bg-gray-400/10'
}

export function erLabel(er: number): string {
  if (er >= 6) return 'Excellent'
  if (er >= 3) return 'Good'
  if (er >= 1) return 'Average'
  return 'Low'
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
