import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './useApi'

export interface Deal {
  id: number
  product_id: number
  retailer_id: number
  deal_type: string
  deal_price: string
  regular_price: string
  discount_percent: string
  deal_score: number
  coupon_code: string | null
  title: string | null
  description: string | null
  source_url: string | null
  image_url: string | null
  is_active: boolean
  is_historical_low: boolean
  found_at: string
  last_seen_at: string
  expires_at: string | null
  product_name: string | null
  product_url: string | null
  product_image: string | null
  retailer_name: string | null
  retailer_slug: string | null
}

export interface DealListResponse {
  deals: Deal[]
  total: number
  offset: number
  limit: number
}

export interface DealStats {
  total_active_deals: number
  avg_discount: number
  best_deal_score: number
  best_deal_title: string | null
  deals_found_today: number
  retailers_monitored: number
  price_errors_found: number
}

export interface DealFilters {
  retailer?: string
  deal_type?: string
  min_score?: number
  min_discount?: number
  max_price?: number
  min_price?: number
  in_stock?: boolean
  search?: string
  sort?: string
  offset?: number
  limit?: number
}

export function useDeals(filters: DealFilters = {}) {
  const params = new URLSearchParams()
  if (filters.retailer) params.set('retailer', filters.retailer)
  if (filters.deal_type) params.set('deal_type', filters.deal_type)
  if (filters.min_score) params.set('min_score', String(filters.min_score))
  if (filters.min_discount) params.set('min_discount', String(filters.min_discount))
  if (filters.max_price) params.set('max_price', String(filters.max_price))
  if (filters.min_price) params.set('min_price', String(filters.min_price))
  if (filters.in_stock !== undefined) params.set('in_stock', String(filters.in_stock))
  if (filters.search) params.set('search', filters.search)
  if (filters.sort) params.set('sort', filters.sort)
  params.set('offset', String(filters.offset ?? 0))
  params.set('limit', String(filters.limit ?? 50))

  return useQuery({
    queryKey: ['deals', filters],
    queryFn: () => apiFetch<DealListResponse>(`/deals?${params}`),
    refetchInterval: 30_000,
  })
}

export function useDealStats() {
  return useQuery({
    queryKey: ['deal-stats'],
    queryFn: () => apiFetch<DealStats>('/deals/stats'),
    refetchInterval: 15_000,
  })
}

export interface PriceHistoryPoint {
  price: string
  original_price: string | null
  coupon_adjusted_price: string | null
  in_stock: boolean
  recorded_at: string
}

export interface PriceHistoryResponse {
  product_id: number
  product_name: string
  history: PriceHistoryPoint[]
  historical_low: string | null
  current_price: string
}

export function usePriceHistory(productId: number | null, days = 30) {
  return useQuery({
    queryKey: ['price-history', productId, days],
    queryFn: () => apiFetch<PriceHistoryResponse>(`/products/${productId}/price-history?days=${days}`),
    enabled: !!productId,
  })
}
