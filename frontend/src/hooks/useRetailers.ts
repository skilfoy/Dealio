import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPatch, apiPost } from './useApi'

export interface Retailer {
  id: number
  name: string
  slug: string
  base_url: string
  logo_url: string | null
  scraper_type: string
  tier: number
  is_enabled: boolean
  requires_api_key: boolean
  rate_limit_ms: number
  scrape_interval_minutes: number
  last_scraped_at: string | null
  success_rate: number
  total_deals_found: number
}

export function useRetailers() {
  return useQuery({
    queryKey: ['retailers'],
    queryFn: () => apiFetch<Retailer[]>('/retailers'),
  })
}

export function useToggleRetailer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, is_enabled }: { slug: string; is_enabled: boolean }) =>
      apiPatch(`/retailers/${slug}`, { is_enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['retailers'] }),
  })
}

export function useTriggerScrape() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiPost(`/retailers/${slug}/scrape`, {}),
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ['scrape-jobs'] }), 2000)
    },
  })
}

export function useScrapeAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<{ count: number; retailers: string[] }>('/retailers/scrape-all', {}),
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ['scrape-jobs'] }), 2000)
    },
  })
}

export function useUpdateRetailer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, ...patch }: { slug: string; rate_limit_ms?: number; scrape_interval_minutes?: number }) =>
      apiPatch(`/retailers/${slug}`, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['retailers'] }),
  })
}
