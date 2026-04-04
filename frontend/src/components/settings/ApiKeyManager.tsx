import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, Trash2, TestTube, ExternalLink, CheckCircle, XCircle, MinusCircle } from 'lucide-react'
import { apiFetch, apiPost, apiDelete } from '../../hooks/useApi'

interface ApiKeyResponse {
  id: number
  service_name: string
  service_slug: string
  category: string
  masked_key: string
  is_valid: boolean | null
  last_tested_at: string | null
  test_status: string | null
}

interface DirectoryEntry {
  service_name: string
  service_slug: string
  category: string
  description: string
  what_it_unlocks: string
  pricing_info: string
  signup_url: string
  is_free_tier: boolean
  is_configured: boolean
}

const CATEGORY_LABELS: Record<string, string> = {
  retailer_api: 'Retailer APIs',
  price_api: 'Price & Deal APIs',
  proxy: 'Proxy & Scraping Services',
  notification: 'Notification Services',
}

function StatusIcon({ status }: { status: boolean | null }) {
  if (status === true) return <CheckCircle className="w-4 h-4 text-green-500" />
  if (status === false) return <XCircle className="w-4 h-4 text-red-500" />
  return <MinusCircle className="w-4 h-4 text-gray-400" />
}

export default function ApiKeyManager() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState<string | null>(null)
  const [newKey, setNewKey] = useState('')

  const { data: directory } = useQuery({
    queryKey: ['api-directory'],
    queryFn: () => apiFetch<DirectoryEntry[]>('/api-keys/directory'),
  })

  const { data: configuredKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => apiFetch<ApiKeyResponse[]>('/api-keys'),
  })

  const addKey = useMutation({
    mutationFn: (entry: DirectoryEntry) =>
      apiPost('/api-keys', {
        service_name: entry.service_name,
        service_slug: entry.service_slug,
        category: entry.category,
        key_value: newKey,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] })
      qc.invalidateQueries({ queryKey: ['api-directory'] })
      setAdding(null)
      setNewKey('')
    },
  })

  const deleteKey = useMutation({
    mutationFn: (id: number) => apiDelete(`/api-keys/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] })
      qc.invalidateQueries({ queryKey: ['api-directory'] })
    },
  })

  const testKey = useMutation({
    mutationFn: (id: number) => apiPost(`/api-keys/${id}/test`, {}),
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ['api-keys'] }), 2000)
    },
  })

  const filtered = directory?.filter((e) =>
    e.service_name.toLowerCase().includes(search.toLowerCase()) ||
    e.description.toLowerCase().includes(search.toLowerCase())
  )

  const grouped = filtered?.reduce((acc, entry) => {
    const cat = entry.category
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(entry)
    return acc
  }, {} as Record<string, DirectoryEntry[]>)

  const configuredMap = new Map(configuredKeys?.map((k) => [k.service_slug, k]))

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          DealRadar works without any API keys. Adding keys unlocks more data sources and higher rate limits.
        </p>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search data sources..."
            className="input pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {grouped && Object.entries(grouped).map(([category, entries]) => (
        <div key={category} className="mb-8">
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            {CATEGORY_LABELS[category] || category}
          </h3>
          <div className="space-y-3">
            {entries.map((entry) => {
              const configured = configuredMap.get(entry.service_slug)
              const isAdding = adding === entry.service_slug

              return (
                <div
                  key={entry.service_slug}
                  className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium">{entry.service_name}</h4>
                        {entry.is_free_tier && (
                          <span className="badge badge-green">Free</span>
                        )}
                        {entry.is_configured && (
                          <StatusIcon status={configured?.is_valid ?? null} />
                        )}
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{entry.description}</p>
                      <p className="text-xs text-blue-500">{entry.what_it_unlocks}</p>
                      <p className="text-xs text-gray-400 mt-1">{entry.pricing_info}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      {configured ? (
                        <>
                          <span className="text-xs font-mono text-gray-500">{configured.masked_key}</span>
                          <button
                            onClick={() => testKey.mutate(configured.id)}
                            className="btn-secondary text-xs"
                            title="Test connection"
                          >
                            <TestTube className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => deleteKey.mutate(configured.id)}
                            className="btn-secondary text-xs text-red-500"
                            title="Remove key"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </>
                      ) : (
                        <>
                          {entry.signup_url && (
                            <a href={entry.signup_url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs">
                              <ExternalLink className="w-3 h-3" />
                              Get Key
                            </a>
                          )}
                          <button onClick={() => setAdding(isAdding ? null : entry.service_slug)} className="btn-primary text-xs">
                            <Plus className="w-3 h-3" />
                            Add Key
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Add key form */}
                  {isAdding && (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="text"
                        className="input flex-1"
                        placeholder="Paste your API key..."
                        value={newKey}
                        onChange={(e) => setNewKey(e.target.value)}
                        autoFocus
                      />
                      <button
                        onClick={() => addKey.mutate(entry)}
                        disabled={!newKey}
                        className="btn-primary disabled:opacity-50"
                      >
                        Save
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
