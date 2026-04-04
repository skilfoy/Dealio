import { useState } from 'react'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { useRetailers } from '../hooks/useRetailers'
import type { DealFilters } from '../hooks/useDeals'

interface Props {
  filters: DealFilters
  onChange: (filters: DealFilters) => void
}

const DEAL_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'price_error', label: 'Price Errors' },
  { value: 'delivery_glitch', label: 'Glitches' },
  { value: 'clearance', label: 'Clearance' },
  { value: 'price_drop', label: 'Price Drops' },
  { value: 'coupon', label: 'Coupons' },
  { value: 'lightning', label: 'Lightning' },
]

const SORT_OPTIONS = [
  { value: 'score', label: 'Best Score' },
  { value: 'discount', label: 'Highest Discount' },
  { value: 'newest', label: 'Newest First' },
  { value: 'price', label: 'Lowest Price' },
]

export default function FilterBar({ filters, onChange }: Props) {
  const { data: retailers } = useRetailers()
  const [showFilters, setShowFilters] = useState(false)

  const update = (partial: Partial<DealFilters>) => {
    onChange({ ...filters, ...partial, offset: 0 })
  }

  return (
    <div className="mb-6 space-y-3">
      {/* Search + toggle */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search deals..."
            className="input pl-10"
            value={filters.search || ''}
            onChange={(e) => update({ search: e.target.value || undefined })}
          />
        </div>
        <select
          className="input w-40"
          value={filters.sort || 'score'}
          onChange={(e) => update({ sort: e.target.value })}
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`btn-secondary ${showFilters ? 'bg-blue-100 dark:bg-blue-900/30' : ''}`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span className="hidden sm:inline">Filters</span>
        </button>
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Retailer</label>
            <select
              className="input"
              value={filters.retailer || ''}
              onChange={(e) => update({ retailer: e.target.value || undefined })}
            >
              <option value="">All Retailers</option>
              {retailers?.map((r) => (
                <option key={r.slug} value={r.slug}>{r.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Deal Type</label>
            <select
              className="input"
              value={filters.deal_type || ''}
              onChange={(e) => update({ deal_type: e.target.value || undefined })}
            >
              {DEAL_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Min Discount: {filters.min_discount || 0}%
            </label>
            <input
              type="range"
              min={0}
              max={95}
              step={5}
              value={filters.min_discount || 0}
              onChange={(e) => update({ min_discount: parseInt(e.target.value) || undefined })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Min Score: {filters.min_score || 0}
            </label>
            <input
              type="range"
              min={0}
              max={95}
              step={5}
              value={filters.min_score || 0}
              onChange={(e) => update({ min_score: parseInt(e.target.value) || undefined })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Max Price ($)</label>
            <input
              type="number"
              className="input"
              placeholder="No max"
              value={filters.max_price ?? ''}
              onChange={(e) => update({ max_price: e.target.value ? parseFloat(e.target.value) : undefined })}
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={filters.in_stock ?? false}
                onChange={(e) => update({ in_stock: e.target.checked || undefined })}
                className="rounded"
              />
              In Stock Only
            </label>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => onChange({ sort: 'score', offset: 0, limit: 50 })}
              className="btn-secondary text-xs"
            >
              <X className="w-3 h-3" />
              Clear All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
