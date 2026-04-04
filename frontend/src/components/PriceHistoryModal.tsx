import { useState } from 'react'
import { X } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { usePriceHistory } from '../hooks/useDeals'

interface Props {
  productId: number
  onClose: () => void
}

export default function PriceHistoryModal({ productId, onClose }: Props) {
  const [days, setDays] = useState(30)
  const { data, isLoading } = usePriceHistory(productId, days)

  const chartData = data?.history.map((p) => ({
    date: new Date(p.recorded_at).toLocaleDateString(),
    price: parseFloat(p.price),
    couponPrice: p.coupon_adjusted_price ? parseFloat(p.coupon_adjusted_price) : null,
  })) || []

  const historicalLow = data?.historical_low ? parseFloat(data.historical_low) : null
  const currentPrice = data?.current_price ? parseFloat(data.current_price) : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 w-full max-w-2xl max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          <div>
            <h2 className="text-lg font-semibold">Price History</h2>
            {data && <p className="text-sm text-gray-500 dark:text-gray-400">{data.product_name}</p>}
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Time range selector */}
        <div className="flex gap-2 px-4 pt-4">
          {[30, 90, 365].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                days === d
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="p-4">
          {isLoading ? (
            <div className="h-64 flex items-center justify-center text-gray-500">Loading...</div>
          ) : chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No price history yet. Data builds over time.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#6b7280" />
                <YAxis tick={{ fontSize: 11 }} stroke="#6b7280" tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                  labelStyle={{ color: '#9ca3af' }}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                />
                <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
                {chartData.some((d) => d.couponPrice !== null) && (
                  <Line type="monotone" dataKey="couponPrice" stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                )}
                {historicalLow && (
                  <ReferenceLine y={historicalLow} stroke="#ef4444" strokeDasharray="3 3" label={{ value: `Low: $${historicalLow.toFixed(2)}`, fill: '#ef4444', fontSize: 11 }} />
                )}
                {currentPrice && (
                  <ReferenceLine y={currentPrice} stroke="#22c55e" strokeDasharray="3 3" label={{ value: `Now: $${currentPrice.toFixed(2)}`, fill: '#22c55e', fontSize: 11 }} />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Stats */}
        {data && historicalLow && (
          <div className="px-4 pb-4 flex gap-4 text-sm">
            <div>
              <span className="text-gray-500">Historical Low: </span>
              <span className="font-semibold text-red-500">${historicalLow.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Current: </span>
              <span className="font-semibold text-green-500">${currentPrice?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">Data Points: </span>
              <span className="font-semibold">{data.history.length}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
