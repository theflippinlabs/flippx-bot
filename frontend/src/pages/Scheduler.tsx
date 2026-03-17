import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Calendar, Plus, Trash2, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import { getScheduledTweets, createScheduledTweet, cancelScheduledTweet } from '../lib/api'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-500/10 text-yellow-400',
  sent: 'bg-emerald-500/10 text-emerald-400',
  failed: 'bg-red-500/10 text-red-400',
  cancelled: 'bg-slate-700 text-slate-400',
}

export default function SchedulerPage() {
  const [content, setContent] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [statusFilter, setStatusFilter] = useState('pending')
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['scheduled-tweets', statusFilter],
    queryFn: () => getScheduledTweets(statusFilter || undefined),
  })

  const createMutation = useMutation({
    mutationFn: () => createScheduledTweet(content, new Date(scheduledAt).toISOString()),
    onSuccess: () => {
      toast.success('Tweet programmé !')
      setContent('')
      setScheduledAt('')
      queryClient.invalidateQueries({ queryKey: ['scheduled-tweets'] })
    },
    onError: (err: Error) => toast.error(`Erreur: ${err.message}`),
  })

  const cancelMutation = useMutation({
    mutationFn: cancelScheduledTweet,
    onSuccess: () => {
      toast.success('Tweet annulé')
      queryClient.invalidateQueries({ queryKey: ['scheduled-tweets'] })
    },
  })

  return (
    <div className="p-4 md:p-8 space-y-4 md:space-y-8">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Scheduler</h1>
        <p className="text-slate-400 mt-0.5 text-sm">Programme tes tweets</p>
      </div>

      {/* Form */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm flex items-center gap-2"><Plus className="w-4 h-4" />Nouveau tweet</h2>
        <textarea
          className="input resize-none h-24 text-sm"
          placeholder="Contenu du tweet..."
          value={content}
          onChange={e => setContent(e.target.value)}
          maxLength={280}
        />
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <label className="block text-xs text-slate-400 mb-1">Date et heure</label>
            <input
              type="datetime-local"
              className="input min-h-[44px]"
              value={scheduledAt}
              onChange={e => setScheduledAt(e.target.value)}
              min={new Date().toISOString().slice(0, 16)}
            />
          </div>
          <div className="flex items-end">
            <button
              className="btn-primary flex items-center gap-2 min-h-[44px] w-full sm:w-auto justify-center"
              disabled={!content.trim() || !scheduledAt || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              <Calendar className="w-4 h-4" />
              Programmer
            </button>
          </div>
        </div>
      </div>

      {/* List */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="font-semibold text-sm">Programmés ({data?.total ?? 0})</h2>
          <select
            className="input w-32 md:w-40 min-h-[44px] text-sm"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="">Tous</option>
            <option value="pending">En attente</option>
            <option value="sent">Envoyés</option>
            <option value="failed">Échoués</option>
            <option value="cancelled">Annulés</option>
          </select>
        </div>

        {data?.tweets?.length === 0 && (
          <p className="text-slate-500 text-sm">Aucun tweet programmé.</p>
        )}

        <div className="space-y-2 md:space-y-3">
          {data?.tweets?.map((tweet: { id: number; content: string; scheduled_at: string; status: string }) => (
            <div key={tweet.id} className="border border-slate-800 rounded-lg p-3 md:p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <p className="text-sm text-slate-200 line-clamp-3">{tweet.content}</p>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {format(new Date(tweet.scheduled_at), 'PPp', { locale: fr })}
                    </span>
                    <span className={`badge ${STATUS_COLORS[tweet.status]}`}>{tweet.status}</span>
                  </div>
                </div>
                {tweet.status === 'pending' && (
                  <button
                    className="text-slate-500 hover:text-red-400 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center shrink-0"
                    onClick={() => cancelMutation.mutate(tweet.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
