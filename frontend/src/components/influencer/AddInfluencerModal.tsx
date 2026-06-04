import * as Dialog from '@radix-ui/react-dialog'
import { X, Plus, Loader2, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { influencerApi } from '@/api/client'
import type { Platform } from '@/types'
import { clsx } from 'clsx'

interface AddInfluencerModalProps {
  open: boolean
  onClose: () => void
}

type Tab = 'manual' | 'csv'
type PlatformOption = { value: Platform; label: string }

const PLATFORMS: PlatformOption[] = [
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
]

interface CsvResult {
  added: number
  skipped: number
  invalid: number
  items: { id: number; platform: string; username: string }[]
}

export function AddInfluencerModal({ open, onClose }: AddInfluencerModalProps) {
  const [tab, setTab] = useState<Tab>('manual')
  const queryClient = useQueryClient()

  // Manual tab state
  const [platform, setPlatform] = useState<Platform>('instagram')
  const [username, setUsername] = useState('')
  const [manualError, setManualError] = useState('')
  const [manualLoading, setManualLoading] = useState(false)

  // CSV tab state
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvLoading, setCsvLoading] = useState(false)
  const [csvResult, setCsvResult] = useState<CsvResult | null>(null)
  const [csvError, setCsvError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleClose() {
    setUsername('')
    setManualError('')
    setCsvFile(null)
    setCsvResult(null)
    setCsvError('')
    onClose()
  }

  // Manual submit
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const clean = username.trim().replace(/^@/, '')
    if (!clean) { setManualError('Please enter a username'); return }
    setManualLoading(true)
    setManualError('')
    try {
      await influencerApi.add(platform, clean)
      queryClient.invalidateQueries({ queryKey: ['influencers'] })
      setUsername('')
      handleClose()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setManualError(msg ?? 'Failed to add influencer. They may already exist.')
    } finally {
      setManualLoading(false)
    }
  }

  // CSV submit
  const handleCsvSubmit = async () => {
    if (!csvFile) return
    setCsvLoading(true)
    setCsvError('')
    setCsvResult(null)
    try {
      const result = await influencerApi.csvUpload(csvFile)
      setCsvResult(result)
      queryClient.invalidateQueries({ queryKey: ['influencers'] })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCsvError(msg ?? 'Failed to process CSV. Check the file format.')
    } finally {
      setCsvLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null
    setCsvFile(f)
    setCsvResult(null)
    setCsvError('')
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl p-6">
          <Dialog.Close className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">
            <X size={16} />
          </Dialog.Close>

          <Dialog.Title className="text-lg font-bold text-white mb-1">Add Influencer</Dialog.Title>
          <Dialog.Description className="text-sm text-gray-500 mb-4">
            Add one by username or import a CSV list
          </Dialog.Description>

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-800 rounded-lg p-0.5 mb-5 border border-gray-700">
            {(['manual', 'csv'] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={clsx(
                  'flex-1 py-1.5 rounded-md text-xs font-medium transition-colors capitalize flex items-center justify-center gap-1.5',
                  tab === t ? 'bg-brand-500 text-white' : 'text-gray-400 hover:text-gray-200'
                )}
              >
                {t === 'csv' ? <><FileText size={12} /> CSV Upload</> : <><Plus size={12} /> Manual</>}
              </button>
            ))}
          </div>

          {tab === 'manual' ? (
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">Platform</label>
                <div className="flex gap-2">
                  {PLATFORMS.map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setPlatform(value)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors border ${
                        platform === value
                          ? 'bg-brand-500/20 border-brand-500 text-brand-400'
                          : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">Username</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">@</span>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => { setUsername(e.target.value); setManualError('') }}
                    placeholder="username (without @)"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-7 pr-3 py-2.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
                    autoFocus
                  />
                </div>
                {manualError && <p className="mt-1.5 text-xs text-red-400">{manualError}</p>}
              </div>

              <button
                type="submit"
                disabled={manualLoading}
                className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                {manualLoading ? <><Loader2 size={14} className="animate-spin" /> Adding & scraping…</> : <><Plus size={14} /> Add & Scrape</>}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              {/* Format hint */}
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-400 space-y-1">
                <p className="font-semibold text-gray-300">CSV format</p>
                <p>Required column: <code className="text-brand-400">username</code></p>
                <p>Optional column: <code className="text-brand-400">platform</code> (instagram / tiktok, defaults to instagram)</p>
                <p className="font-mono text-gray-500 mt-1">platform,username<br />instagram,azzaslimene<br />tiktok,monacostarica</p>
              </div>

              {/* File picker */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className={clsx(
                  'border-2 border-dashed rounded-lg p-6 flex flex-col items-center gap-2 cursor-pointer transition-colors',
                  csvFile ? 'border-brand-500/50 bg-brand-500/5' : 'border-gray-700 hover:border-gray-600 bg-gray-800/30'
                )}
              >
                <Upload size={20} className={csvFile ? 'text-brand-400' : 'text-gray-500'} />
                {csvFile ? (
                  <p className="text-sm text-brand-400 font-medium">{csvFile.name}</p>
                ) : (
                  <p className="text-sm text-gray-400">Click to choose a CSV file</p>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>

              {csvError && (
                <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  <AlertCircle size={12} />
                  {csvError}
                </div>
              )}

              {csvResult && (
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 space-y-2">
                  <div className="flex items-center gap-2 text-green-400 text-sm font-medium">
                    <CheckCircle size={14} />
                    Import complete
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-center">
                    <div className="bg-green-500/10 border border-green-500/20 rounded-lg py-2">
                      <div className="text-green-400 font-bold text-lg">{csvResult.added}</div>
                      <div className="text-gray-400">Added</div>
                    </div>
                    <div className="bg-gray-700/30 border border-gray-700 rounded-lg py-2">
                      <div className="text-gray-300 font-bold text-lg">{csvResult.skipped}</div>
                      <div className="text-gray-400">Skipped</div>
                    </div>
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg py-2">
                      <div className="text-red-400 font-bold text-lg">{csvResult.invalid}</div>
                      <div className="text-gray-400">Invalid</div>
                    </div>
                  </div>
                  {csvResult.added > 0 && (
                    <p className="text-xs text-gray-500">Scraping queued for {csvResult.added} influencer{csvResult.added !== 1 ? 's' : ''}.</p>
                  )}
                </div>
              )}

              {!csvResult && (
                <button
                  onClick={handleCsvSubmit}
                  disabled={!csvFile || csvLoading}
                  className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
                >
                  {csvLoading ? <><Loader2 size={14} className="animate-spin" /> Importing…</> : <><Upload size={14} /> Import & Scrape</>}
                </button>
              )}

              {csvResult && (
                <button
                  onClick={handleClose}
                  className="w-full flex items-center justify-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
                >
                  Done
                </button>
              )}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
