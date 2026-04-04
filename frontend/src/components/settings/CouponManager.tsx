import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, CheckCircle, XCircle } from 'lucide-react'
import { apiFetch, apiPost, apiDelete } from '../../hooks/useApi'
import { useRetailers } from '../../hooks/useRetailers'

interface Coupon {
  id: number
  retailer_id: number
  code: string
  description: string | null
  discount_type: string
  discount_value: string
  is_verified: boolean
  last_tested_at: string | null
  success_rate: number
  times_used: number
  expires_at: string | null
}

export default function CouponManager() {
  const qc = useQueryClient()
  const { data: retailers } = useRetailers()
  const [selectedRetailer, setSelectedRetailer] = useState<number | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newDesc, setNewDesc] = useState('')

  const { data: coupons } = useQuery({
    queryKey: ['coupons', selectedRetailer],
    queryFn: () => apiFetch<Coupon[]>(`/coupons${selectedRetailer ? `?retailer_id=${selectedRetailer}` : ''}`),
  })

  const addCoupon = useMutation({
    mutationFn: () =>
      apiPost('/coupons', {
        retailer_id: selectedRetailer,
        code: newCode,
        description: newDesc || null,
        discount_type: 'percent',
        discount_value: 0,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['coupons'] })
      setNewCode('')
      setNewDesc('')
      setShowAdd(false)
    },
  })

  const deleteCoupon = useMutation({
    mutationFn: (id: number) => apiDelete(`/coupons/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coupons'] }),
  })

  return (
    <div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Manage coupon codes by retailer. Verified codes are applied to deal price calculations.
      </p>

      <div className="flex gap-3 mb-4">
        <select
          className="input w-60"
          value={selectedRetailer ?? ''}
          onChange={(e) => setSelectedRetailer(e.target.value ? parseInt(e.target.value) : null)}
        >
          <option value="">All Retailers</option>
          {retailers?.map((r) => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary" disabled={!selectedRetailer}>
          <Plus className="w-4 h-4" />
          Add Coupon
        </button>
      </div>

      {/* Add form */}
      {showAdd && selectedRetailer && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 mb-4 flex gap-3">
          <input
            type="text"
            className="input flex-1"
            placeholder="Coupon code (e.g. SAVE20)"
            value={newCode}
            onChange={(e) => setNewCode(e.target.value.toUpperCase())}
          />
          <input
            type="text"
            className="input flex-1"
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
          />
          <button onClick={() => addCoupon.mutate()} disabled={!newCode} className="btn-primary disabled:opacity-50">
            Save
          </button>
        </div>
      )}

      {/* Coupon list */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 divide-y divide-gray-100 dark:divide-gray-800">
        {(!coupons || coupons.length === 0) ? (
          <div className="p-8 text-center text-sm text-gray-500">
            No coupons yet. Select a retailer and add coupon codes to track.
          </div>
        ) : (
          coupons.map((c) => (
            <div key={c.id} className="flex items-center justify-between p-3">
              <div className="flex items-center gap-3">
                {c.is_verified ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-gray-400" />
                )}
                <div>
                  <span className="font-mono font-semibold text-sm">{c.code}</span>
                  {c.description && (
                    <span className="text-xs text-gray-500 ml-2">{c.description}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Used {c.times_used}x</span>
                <span>{(c.success_rate * 100).toFixed(0)}% success</span>
                <button
                  onClick={() => deleteCoupon.mutate(c.id)}
                  className="text-red-500 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
