import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Deal } from './useDeals'

interface ScanProgress {
  retailer: string
  items_found: number
  deals_found: number
}

export function useSSE() {
  const queryClient = useQueryClient()
  const [liveFeed, setLiveFeed] = useState<Deal[]>([])
  const [scanProgress, setScanProgress] = useState<ScanProgress[]>([])
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const es = new EventSource('/api/deals/stream')
    eventSourceRef.current = es

    es.addEventListener('connected', () => {
      setConnected(true)
    })

    es.addEventListener('new_deal', (event) => {
      try {
        const deal = JSON.parse(event.data) as Deal
        setLiveFeed((prev) => [deal, ...prev].slice(0, 100))
        // Invalidate deals query to refresh the grid
        queryClient.invalidateQueries({ queryKey: ['deals'] })
        queryClient.invalidateQueries({ queryKey: ['deal-stats'] })
      } catch (e) {
        // ignore parse errors
      }
    })

    es.addEventListener('scan_progress', (event) => {
      try {
        const progress = JSON.parse(event.data) as ScanProgress
        setScanProgress((prev) => {
          const existing = prev.findIndex((p) => p.retailer === progress.retailer)
          if (existing >= 0) {
            const updated = [...prev]
            updated[existing] = progress
            return updated
          }
          return [progress, ...prev].slice(0, 20)
        })
      } catch (e) {
        // ignore
      }
    })

    es.addEventListener('heartbeat', () => {
      setConnected(true)
    })

    es.onerror = () => {
      setConnected(false)
      es.close()
      // Reconnect after 5 seconds
      setTimeout(connect, 5000)
    }
  }, [queryClient])

  useEffect(() => {
    connect()
    return () => {
      eventSourceRef.current?.close()
    }
  }, [connect])

  return { liveFeed, scanProgress, connected }
}
