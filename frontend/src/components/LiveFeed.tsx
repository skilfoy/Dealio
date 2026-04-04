import { Zap, Radio } from 'lucide-react'
import { useSSE } from '../hooks/useSSE'
import type { Deal } from '../hooks/useDeals'
import CouponBadge from './CouponBadge'

function LiveDealItem({ deal }: { deal: Deal }) {
  const discount = parseFloat(deal.discount_percent || '0')
  const price = parseFloat(deal.deal_price || '0')

  const discountColor =
    discount >= 85 ? 'text-red-400' :
    discount >= 70 ? 'text-amber-400' :
    'text-green-400'

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-800/50 transition-colors animate-slide-in">
      {deal.product_image && (
        <img
          src={deal.product_image}
          alt=""
          className="w-10 h-10 rounded object-contain bg-gray-800 flex-shrink-0"
          loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm truncate">{deal.product_name || deal.title || 'New Deal'}</div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-400">{deal.retailer_name}</span>
          <span className="font-bold text-green-400">${price.toFixed(2)}</span>
          <span className={`font-semibold ${discountColor}`}>{discount.toFixed(0)}% off</span>
        </div>
      </div>
      {deal.coupon_code && <CouponBadge code={deal.coupon_code} />}
    </div>
  )
}

export default function LiveFeed() {
  const { liveFeed, scanProgress, connected } = useSSE()

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
        <Radio className={`w-4 h-4 ${connected ? 'text-red-500 animate-pulse' : 'text-gray-600'}`} />
        <span className="text-sm font-semibold text-gray-200">Live Feed</span>
        {liveFeed.length > 0 && (
          <span className="text-xs text-gray-500">{liveFeed.length} deals</span>
        )}
      </div>

      {/* Scan progress */}
      {scanProgress.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-800/50 space-y-1">
          {scanProgress.slice(0, 3).map((p) => (
            <div key={p.retailer} className="flex items-center gap-2 text-xs text-gray-400">
              <Zap className="w-3 h-3 text-amber-500" />
              <span>Scanning {p.retailer}...</span>
              <span className="text-green-400">{p.deals_found} deals</span>
            </div>
          ))}
        </div>
      )}

      {/* Feed items */}
      <div className="max-h-96 overflow-y-auto">
        {liveFeed.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            {connected ? 'Waiting for deals...' : 'Connecting to live stream...'}
          </div>
        ) : (
          <div className="divide-y divide-gray-800/50">
            {liveFeed.slice(0, 20).map((deal, i) => (
              <LiveDealItem key={`${deal.id}-${i}`} deal={deal} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
