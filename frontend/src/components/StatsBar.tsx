import { TrendingDown, Tag, Zap, Store, AlertTriangle } from 'lucide-react'
import { useDealStats } from '../hooks/useDeals'

export default function StatsBar() {
  const { data: stats } = useDealStats()

  const items = [
    {
      label: 'Active Deals',
      value: stats?.total_active_deals ?? 0,
      icon: Tag,
      color: 'text-blue-500',
    },
    {
      label: 'Avg Discount',
      value: stats ? `${stats.avg_discount}%` : '0%',
      icon: TrendingDown,
      color: 'text-green-500',
    },
    {
      label: 'Best Score',
      value: stats?.best_deal_score ?? 0,
      icon: Zap,
      color: 'text-amber-500',
    },
    {
      label: 'Found Today',
      value: stats?.deals_found_today ?? 0,
      icon: Tag,
      color: 'text-purple-500',
    },
    {
      label: 'Retailers',
      value: stats?.retailers_monitored ?? 0,
      icon: Store,
      color: 'text-indigo-500',
    },
    {
      label: 'Price Errors',
      value: stats?.price_errors_found ?? 0,
      icon: AlertTriangle,
      color: 'text-red-500',
    },
  ]

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-6">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <div
            key={item.label}
            className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-3 text-center"
          >
            <Icon className={`w-5 h-5 mx-auto mb-1 ${item.color}`} />
            <div className="text-lg font-bold">{item.value}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{item.label}</div>
          </div>
        )
      })}
    </div>
  )
}
