import { Users } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <div className="p-4 rounded-full bg-gray-800">
        <Users size={32} className="text-gray-500" />
      </div>
      <div>
        <p className="text-gray-300 font-semibold text-lg">{title}</p>
        {description && <p className="text-gray-500 text-sm mt-1">{description}</p>}
      </div>
      {action}
    </div>
  )
}
