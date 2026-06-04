import { clsx } from 'clsx'

export function LoadingSpinner({ size = 'md', className }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const s = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }[size]
  return (
    <div
      className={clsx('animate-spin rounded-full border-2 border-gray-600 border-t-brand-500', s, className)}
      role="status"
    />
  )
}
