import * as Dialog from '@radix-ui/react-dialog'
import { X, Plus, Loader2, Instagram, Music2 } from 'lucide-react'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { brandApi } from '@/api/client'
import type { BudgetTier } from '@/types'

const NICHES = [
  'Fashion', 'Beauty', 'Food & Beverage', 'Travel', 'Fitness',
  'Lifestyle', 'Tech', 'Business', 'Art & Culture', 'Entertainment',
  'Education', 'Environment',
]

const TIERS: { value: BudgetTier; label: string; desc: string }[] = [
  { value: 'nano', label: 'Nano', desc: '< 10K' },
  { value: 'micro', label: 'Micro', desc: '10K – 100K' },
  { value: 'macro', label: 'Macro', desc: '100K – 1M' },
  { value: 'mega', label: 'Mega', desc: '1M+' },
]

interface AddBrandModalProps {
  open: boolean
  onClose: () => void
}

export function AddBrandModal({ open, onClose }: AddBrandModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [igLink, setIgLink] = useState('')
  const [ttLink, setTtLink] = useState('')
  const [categories, setCategories] = useState<string[]>([])
  const [budgetTier, setBudgetTier] = useState<BudgetTier>('micro')
  const [minEr, setMinEr] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const queryClient = useQueryClient()

  const toggleCategory = (cat: string) => {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    )
  }

  const handleClose = () => {
    setName(''); setDescription(''); setIgLink(''); setTtLink('')
    setCategories([]); setBudgetTier('micro'); setMinEr(''); setError('')
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Please enter a brand name'); return }

    setIsLoading(true)
    setError('')
    try {
      const brand = await brandApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        ig_link: igLink.trim() || undefined,
        tt_link: ttLink.trim() || undefined,
        categories,
        budget_tier: budgetTier,
        min_er: parseFloat(minEr) || 0,
      })
      // Fire-and-forget: fetch IG profile pic in the background
      if (igLink.trim()) {
        brandApi.fetchIg(brand.id)
          .then(() => queryClient.invalidateQueries({ queryKey: ['brands'] }))
          .catch(() => {})
      }
      queryClient.invalidateQueries({ queryKey: ['brands'] })
      handleClose()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to create brand')
    } finally {
      setIsLoading(false)
    }
  }

  const platformLabel = igLink && ttLink
    ? 'Instagram + TikTok'
    : igLink
    ? 'Instagram only'
    : ttLink
    ? 'TikTok only'
    : 'All platforms'

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto">
          <Dialog.Close className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">
            <X size={16} />
          </Dialog.Close>

          <Dialog.Title className="text-lg font-bold text-white mb-1">Add Brand</Dialog.Title>
          <Dialog.Description className="text-sm text-gray-500 mb-5">
            Define the brand's targeting criteria to find matching influencers
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">Brand Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); setError('') }}
                placeholder="e.g. Vitalait, L'Oréal"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
                autoFocus
              />
            </div>

            {/* Description */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief notes about this brand or campaign…"
                rows={2}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors resize-none"
              />
            </div>

            {/* Social links */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
                Social Profiles
                <span className="text-gray-600 normal-case font-normal ml-1">
                  — determines which platform to target · {platformLabel}
                </span>
              </label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="shrink-0 w-8 flex justify-center">
                    <Instagram size={16} className="text-pink-400" />
                  </span>
                  <input
                    type="text"
                    value={igLink}
                    onChange={(e) => setIgLink(e.target.value)}
                    placeholder="https://www.instagram.com/brandname"
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-pink-500 transition-colors"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <span className="shrink-0 w-8 flex justify-center">
                    <Music2 size={16} className="text-cyan-400" />
                  </span>
                  <input
                    type="text"
                    value={ttLink}
                    onChange={(e) => setTtLink(e.target.value)}
                    placeholder="https://www.tiktok.com/@brandname"
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-1.5">
                The IG profile picture will be fetched automatically if an Instagram link is provided.
              </p>
            </div>

            {/* Categories */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
                Target Niches
                <span className="text-gray-600 normal-case font-normal ml-1">(select all that apply)</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {NICHES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => toggleCategory(cat)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors border ${
                      categories.includes(cat)
                        ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Budget tier */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">Influencer Tier</label>
              <div className="grid grid-cols-4 gap-2">
                {TIERS.map(({ value, label, desc }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setBudgetTier(value)}
                    className={`py-2 px-1 rounded-lg text-center transition-colors border ${
                      budgetTier === value
                        ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <div className="text-sm font-medium">{label}</div>
                    <div className="text-xs text-gray-500">{desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Min ER */}
            <div>
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
                Min Engagement Rate %
                <span className="text-gray-600 normal-case font-normal ml-1">(0 = no minimum)</span>
              </label>
              <input
                type="number"
                value={minEr}
                onChange={(e) => setMinEr(e.target.value)}
                placeholder="e.g. 2.5"
                min={0}
                step={0.1}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
              />
            </div>

            {error && <p className="text-xs text-red-400">{error}</p>}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
            >
              {isLoading
                ? <><Loader2 size={14} className="animate-spin" /> Saving…</>
                : <><Plus size={14} /> Add Brand</>
              }
            </button>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
