import { useState } from 'react'
import { Play, Loader2, CheckCircle } from 'lucide-react'
import { useDeals, type DealFilters } from '../hooks/useDeals'
import { useScrapeAll } from '../hooks/useRetailers'
import StatsBar from '../components/StatsBar'
import FilterBar from '../components/FilterBar'
import LiveFeed from '../components/LiveFeed'
import DealGrid from '../components/DealGrid'
import PriceHistoryModal from '../components/PriceHistoryModal'

export default function Dashboard() {
  const [filters, setFilters] = useState<DealFilters>({ sort: 'score', limit: 50, offset: 0 })
  const [historyProductId, setHistoryProductId] = useState<number | null>(null)
  const { data, isLoading } = useDeals(filters)
  const scrapeAll = useScrapeAll()

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <StatsBar />
        <button
          onClick={() => scrapeAll.mutate()}
          disabled={scrapeAll.isPending || scrapeAll.isSuccess}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg transition-colors shrink-0"
        >
          {scrapeAll.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Queuing...</>
          ) : scrapeAll.isSuccess ? (
            <><CheckCircle className="w-4 h-4" /> Queued {(scrapeAll.data as any)?.count ?? ''} scrapers</>
          ) : (
            <><Play className="w-4 h-4" /> Run All Available</>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Live Feed — sidebar on desktop, top on mobile */}
        <div className="lg:col-span-1 order-first lg:order-last">
          <LiveFeed />
        </div>

        {/* Main content */}
        <div className="lg:col-span-3">
          <FilterBar filters={filters} onChange={setFilters} />
          <DealGrid
            deals={data?.deals ?? []}
            total={data?.total ?? 0}
            loading={isLoading}
            offset={filters.offset ?? 0}
            limit={filters.limit ?? 50}
            onPageChange={(offset) => setFilters((prev) => ({ ...prev, offset }))}
            onViewHistory={setHistoryProductId}
          />
        </div>
      </div>

      {/* Price history modal */}
      {historyProductId && (
        <PriceHistoryModal
          productId={historyProductId}
          onClose={() => setHistoryProductId(null)}
        />
      )}
    </div>
  )
}
