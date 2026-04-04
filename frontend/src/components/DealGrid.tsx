import { Loader2 } from 'lucide-react'
import type { Deal } from '../hooks/useDeals'
import DealCard from './DealCard'

interface Props {
  deals: Deal[]
  total: number
  loading: boolean
  offset: number
  limit: number
  onPageChange: (offset: number) => void
  onViewHistory: (productId: number) => void
}

export default function DealGrid({ deals, total, loading, offset, limit, onPageChange, onViewHistory }: Props) {
  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(offset / limit) + 1

  if (loading && deals.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-500">Loading deals...</span>
      </div>
    )
  }

  if (deals.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500 dark:text-gray-400">
        <p className="text-lg font-medium mb-2">No deals found</p>
        <p className="text-sm">Try adjusting your filters or wait for scrapers to discover new deals.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {deals.map((deal) => (
          <DealCard key={deal.id} deal={deal} onViewHistory={onViewHistory} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => onPageChange(Math.max(0, offset - limit))}
            disabled={offset === 0}
            className="btn-secondary disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500 dark:text-gray-400 px-3">
            Page {currentPage} of {totalPages} ({total} deals)
          </span>
          <button
            onClick={() => onPageChange(offset + limit)}
            disabled={offset + limit >= total}
            className="btn-secondary disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
