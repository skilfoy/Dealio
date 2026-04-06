import { useState } from 'react'
import { Play, Loader2, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useRetailers, useToggleRetailer, useTriggerScrape, useUpdateRetailer } from '../../hooks/useRetailers'

const TIER_LABELS: Record<number, string> = {
  1: 'Tier 1 — API',
  2: 'Tier 2 — Browser',
  3: 'Tier 3 — Outlet/RSS',
}

function SpeedEditor({ slug, rateLimitMs, intervalMin }: { slug: string; rateLimitMs: number; intervalMin: number }) {
  const update = useUpdateRetailer()
  const [rl, setRl] = useState(rateLimitMs)
  const [iv, setIv] = useState(intervalMin)

  const save = () => {
    if (rl !== rateLimitMs || iv !== intervalMin) {
      update.mutate({ slug, rate_limit_ms: rl, scrape_interval_minutes: iv })
    }
  }

  return (
    <div className="px-3 pb-3 pt-1 flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50">
      <label className="flex items-center gap-2">
        Delay between requests
        <input
          type="number"
          min={100}
          max={30000}
          step={100}
          value={rl}
          onChange={(e) => setRl(Number(e.target.value))}
          onBlur={save}
          className="w-20 px-1.5 py-0.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-xs"
        />
        ms
      </label>
      <label className="flex items-center gap-2">
        Scrape every
        <input
          type="number"
          min={5}
          max={1440}
          step={5}
          value={iv}
          onChange={(e) => setIv(Number(e.target.value))}
          onBlur={save}
          className="w-16 px-1.5 py-0.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-xs"
        />
        min
      </label>
      {update.isPending && <span className="text-blue-500">Saving…</span>}
      {update.isSuccess && <span className="text-green-500">Saved</span>}
    </div>
  )
}

function RetailerRow({ r }: { r: ReturnType<typeof useRetailers>['data'] extends (infer T)[] | undefined ? T : never }) {
  const toggleMutation = useToggleRetailer()
  const scrapeMutation = useTriggerScrape()
  const [expanded, setExpanded] = useState(false)

  return (
    <div>
      <div className="flex items-center justify-between p-3 gap-4">
        <div className="flex items-center gap-3 flex-1">
          <button
            onClick={() => toggleMutation.mutate({ slug: r.slug, is_enabled: !r.is_enabled })}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              r.is_enabled ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-700'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                r.is_enabled ? 'translate-x-5' : ''
              }`}
            />
          </button>
          <div>
            <span className="text-sm font-medium">{r.name}</span>
            {r.requires_api_key && (
              <span className="ml-2 text-xs text-amber-500">Requires API key</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span className="hidden sm:inline">{r.scraper_type}</span>
          <span>{r.total_deals_found} deals</span>
          {r.last_scraped_at && (
            <span className="hidden md:inline">{new Date(r.last_scraped_at).toLocaleTimeString()}</span>
          )}
          <button
            onClick={() => scrapeMutation.mutate(r.slug)}
            disabled={!r.is_enabled || scrapeMutation.isPending}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30 transition-colors"
            title="Trigger scrape now"
          >
            {scrapeMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500" />
            ) : scrapeMutation.isSuccess ? (
              <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Speed settings"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <SpeedEditor
          slug={r.slug}
          rateLimitMs={r.rate_limit_ms}
          intervalMin={r.scrape_interval_minutes}
        />
      )}
    </div>
  )
}

export default function RetailerManager() {
  const { data: retailers } = useRetailers()

  const grouped = retailers?.reduce((acc, r) => {
    if (!acc[r.tier]) acc[r.tier] = []
    acc[r.tier].push(r)
    return acc
  }, {} as Record<number, typeof retailers>)

  return (
    <div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Enable or disable retailers. Click the chevron to adjust per-scraper speed and interval.
      </p>

      {grouped && [1, 2, 3].map((tier) => {
        const items = grouped[tier]
        if (!items?.length) return null
        return (
          <div key={tier} className="mb-8">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              {TIER_LABELS[tier]}
            </h3>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 divide-y divide-gray-100 dark:divide-gray-800">
              {items.map((r) => <RetailerRow key={r.slug} r={r} />)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
