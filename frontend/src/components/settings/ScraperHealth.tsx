import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, Loader2, Clock } from 'lucide-react'
import { apiFetch } from '../../hooks/useApi'

interface ScrapeJob {
  id: number
  retailer_id: number
  status: string
  items_found: number
  deals_found: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  retailer_name: string | null
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />
    case 'running':
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
    default:
      return <Clock className="w-4 h-4 text-gray-400" />
  }
}

export default function ScraperHealth() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['scrape-jobs'],
    queryFn: () => apiFetch<ScrapeJob[]>('/scrape-jobs?limit=100'),
    refetchInterval: 10_000,
  })

  if (isLoading) {
    return <div className="flex items-center gap-2 text-gray-500"><Loader2 className="w-5 h-5 animate-spin" /> Loading...</div>
  }

  return (
    <div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Real-time status of all scraper workers. Jobs refresh every 10 seconds.
      </p>

      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-800">
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Status</th>
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Retailer</th>
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Items</th>
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Deals</th>
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Time</th>
              <th className="text-left p-3 font-medium text-gray-500 dark:text-gray-400">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {(!jobs || jobs.length === 0) ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-gray-500">
                  No scrape jobs yet. Trigger a scrape from the Retailers tab or wait for the scheduler.
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.id}>
                  <td className="p-3"><StatusIcon status={job.status} /></td>
                  <td className="p-3 font-medium">{job.retailer_name || `#${job.retailer_id}`}</td>
                  <td className="p-3">{job.items_found}</td>
                  <td className="p-3">
                    <span className={job.deals_found > 0 ? 'text-green-500 font-semibold' : ''}>
                      {job.deals_found}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-gray-500">
                    {job.completed_at
                      ? new Date(job.completed_at).toLocaleTimeString()
                      : job.started_at
                        ? 'Running...'
                        : 'Pending'}
                  </td>
                  <td className="p-3 text-xs text-red-500 max-w-xs truncate">{job.error_message}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
