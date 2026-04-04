import { ExternalLink, TrendingDown, History } from 'lucide-react'
import clsx from 'clsx'
import type { Deal } from '../hooks/useDeals'
import DealScoreBadge from './DealScoreBadge'
import CouponBadge from './CouponBadge'

function DiscountBadge({ percent }: { percent: number }) {
  const color =
    percent >= 85 ? 'badge-red' :
    percent >= 70 ? 'badge-amber' :
    'badge-green'

  return <span className={`badge ${color}`}>{percent.toFixed(0)}% off</span>
}

function DealTypeBadge({ type }: { type: string }) {
  const labels: Record<string, { label: string; className: string }> = {
    price_error: { label: 'PRICE ERROR', className: 'bg-red-500 text-white' },
    delivery_glitch: { label: 'GLITCH', className: 'bg-red-500 text-white animate-pulse-slow' },
    clearance: { label: 'Clearance', className: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400' },
    lightning: { label: 'Lightning', className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' },
    coupon: { label: 'Coupon', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' },
    price_drop: { label: 'Price Drop', className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' },
  }
  const info = labels[type] || { label: type, className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300' }
  return <span className={`badge ${info.className}`}>{info.label}</span>
}

interface Props {
  deal: Deal
  onViewHistory?: (productId: number) => void
}

export default function DealCard({ deal, onViewHistory }: Props) {
  const discount = parseFloat(deal.discount_percent)
  const dealPrice = parseFloat(deal.deal_price)
  const regularPrice = parseFloat(deal.regular_price)

  return (
    <div className="deal-card flex flex-col gap-3 animate-slide-in">
      {/* Header: badges */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <DealTypeBadge type={deal.deal_type} />
          <DiscountBadge percent={discount} />
          {deal.is_historical_low && (
            <span className="badge bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
              Historical Low
            </span>
          )}
        </div>
        <DealScoreBadge score={deal.deal_score} />
      </div>

      {/* Product info */}
      <div className="flex gap-3">
        {/* Image */}
        {(deal.product_image || deal.image_url) && (
          <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
            <img
              src={deal.product_image || deal.image_url || ''}
              alt=""
              className="w-full h-full object-contain"
              loading="lazy"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium line-clamp-2 mb-1">
            {deal.product_name || deal.title || 'Deal'}
          </h3>
          {deal.retailer_name && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {deal.retailer_name}
            </span>
          )}
        </div>
      </div>

      {/* Price */}
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-green-600 dark:text-green-400">
          ${dealPrice.toFixed(2)}
        </span>
        {regularPrice > dealPrice && (
          <span className="text-sm text-gray-400 line-through">
            ${regularPrice.toFixed(2)}
          </span>
        )}
      </div>

      {/* Coupon code */}
      {deal.coupon_code && (
        <CouponBadge code={deal.coupon_code} />
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto">
        <a
          href={deal.product_url || deal.source_url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary flex-1 justify-center text-center"
        >
          <ExternalLink className="w-4 h-4" />
          View Deal
        </a>
        {onViewHistory && (
          <button
            onClick={() => onViewHistory(deal.product_id)}
            className="btn-secondary"
            title="Price History"
          >
            <History className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Time */}
      <div className="text-xs text-gray-400">
        Found {new Date(deal.found_at).toLocaleString()}
      </div>
    </div>
  )
}
