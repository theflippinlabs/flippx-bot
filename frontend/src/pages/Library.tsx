import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { BookOpen, Trash2, Clock, CheckCircle, XCircle, AlertCircle, Filter } from 'lucide-react'
import toast from 'react-hot-toast'
import { getLibrary, deleteTweet } from '../lib/api'

type Tweet = {
  id: number
  content: string
  status: string
  priority: number
  created_at: string
  sent_at?: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: 'Pending', color: 'text-yellow-400 bg-yellow-400/10', icon: Clock },
  sent: { label: 'Posted', color: 'text-emerald-400 bg-emerald-400/10', icon: CheckCircle },
  failed: { label: 'Failed', color: 'text-red-400 bg-red-400/10', icon: AlertCircle },
  cancelled: { label: 'Cancelled', color: 'text-slate-400 bg-slate-400/10', icon: XCircle },
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function LibraryPage() {
  const [filter, setFilter] = useState<string>('')
  const [page, setPage] = useState(0)
  const queryClient = useQueryClient()
  const limit = 50

  const { data, isLoading } = useQuery({
    queryKey: ['library', filter, page],
    queryFn: () => getLibrary(filter || undefined, page * limit, limit),
    refetchInterval: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTweet,
    onSuccess: () => {
      toast.success('Tweet deleted')
      queryClient.invalidateQueries({ queryKey: ['library'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const tweets: Tweet[] = data?.tweets ?? []
  const total: number = data?.total ?? 0
  const totalPages = Math.ceil(total / limit)

  const filters = [
    { value: '', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'sent', label: 'Posted' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  return (
    <div className="p-4 md:p-8 space-y-4 md:space-y-6">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
            <BookOpen className="w-5 md:w-6 h-5 md:h-6 text-sky-400" />
            Library
          </h1>
          <p className="text-slate-400 text-sm">{total} tweets</p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1 overflow-x-auto">
          <Filter className="w-4 h-4 text-slate-500 ml-2 shrink-0" />
          {filters.map(f => (
            <button
              key={f.value}
              onClick={() => { setFilter(f.value); setPage(0) }}
              className={`px-3 py-2 rounded-md text-xs font-medium transition-colors whitespace-nowrap min-h-[36px] ${
                filter === f.value
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tweet list */}
      <div className="space-y-2">
        {isLoading && (
          <div className="text-center py-12 text-slate-500">Loading...</div>
        )}

        {!isLoading && tweets.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500">No tweets found</p>
          </div>
        )}

        {tweets.map((tweet) => {
          const cfg = STATUS_CONFIG[tweet.status] || STATUS_CONFIG.pending
          const StatusIcon = cfg.icon
          return (
            <div
              key={tweet.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap break-words">
                    {tweet.content}
                  </p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
                      <StatusIcon className="w-3 h-3" />
                      {cfg.label}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatDate(tweet.created_at)}
                    </span>
                    {tweet.sent_at && (
                      <span className="text-xs text-slate-500">
                        Posted {formatDate(tweet.sent_at)}
                      </span>
                    )}
                    <span className="text-xs text-slate-600">
                      {tweet.content.length}/280
                    </span>
                  </div>
                </div>

                {/* Delete button (only for non-sent tweets) */}
                {tweet.status !== 'sent' && (
                  <button
                    onClick={() => deleteMutation.mutate(tweet.id)}
                    disabled={deleteMutation.isPending}
                    className="text-slate-600 hover:text-red-400 transition-colors shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center"
                    title="Delete tweet"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2 md:pt-4">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30 transition-colors min-h-[44px]"
          >
            Prev
          </button>
          <span className="text-sm text-slate-500">
            {page + 1}/{totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-900 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30 transition-colors min-h-[44px]"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
