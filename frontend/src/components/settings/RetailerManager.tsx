import { Play, Pause } from 'lucide-react'
import { useRetailers, useToggleRetailer, useTriggerScrape } from '../../hooks/useRetailers'

const TIER_LABELS: Record<number, string> = {
  1: 'Tier 1 — API',
  2: 'Tier 2 — Browser',
  3: 'Tier 3 — Outlet/RSS',
}

export default function RetailerManager() {
  const { data: retailers } = useRetailers()
  const toggleMutation = useToggleRetailer()
  const scrapeMutation = useTriggerScrape()

  const grouped = retailers?.reduce((acc, r) => {
    if (!acc[r.tier]) acc[r.tier] = []
    acc[r.tier].push(r)
    return acc
  }, {} as Record<number, typeof retailers>)

  return (
    <div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Enable or disable individual retailers. Tier 1 sources use APIs and are most reliable.
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
              {items.map((r) => (
                <div key={r.slug} className="flex items-center justify-between p-3 gap-4">
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

                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <span>{r.scraper_type}</span>
                    <span>{r.total_deals_found} deals</span>
                    {r.last_scraped_at && (
                      <span>{new Date(r.last_scraped_at).toLocaleTimeString()}</span>
                    )}
                    <button
                      onClick={() => scrapeMutation.mutate(r.slug)}
                      disabled={!r.is_enabled}
                      className="btn-secondary text-xs disabled:opacity-30"
                      title="Trigger scrape now"
                    >
                      <Play className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
