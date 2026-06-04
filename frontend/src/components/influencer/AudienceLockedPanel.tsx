import { Lock } from 'lucide-react'

export function AudienceLockedPanel() {
  return (
    <div className="bg-gray-800/50 rounded-xl p-4 flex flex-col items-center justify-center gap-2 min-h-[120px]">
      <Lock size={18} className="text-gray-600" />
      <p className="text-xs text-gray-500 text-center leading-relaxed">
        Audience demographics require the Instagram Business API with influencer consent.
      </p>
    </div>
  )
}
