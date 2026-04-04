import { useState } from 'react'
import { useDeals, type DealFilters } from '../hooks/useDeals'
import StatsBar from '../components/StatsBar'
import FilterBar from '../components/FilterBar'
import LiveFeed from '../components/LiveFeed'
import DealGrid from '../components/DealGrid'
import PriceHistoryModal from '../components/PriceHistoryModal'

export default function Dashboard() {
  const [filters, setFilters] = useState<DealFilters>({ sort: 'score', limit: 50, offset: 0 })
  const [historyProductId, setHistoryProductId] = useState<number | null>(null)
  const { data, isLoading } = useDeals(filters)

  return (
    <div>
      <StatsBar />

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
