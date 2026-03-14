import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Send, Twitter, Heart, Repeat2, Eye, MessageCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getProfile, getBotStatus, sendTweet, getTweetLogs } from '../lib/api'
import { formatDistanceToNow } from 'date-fns'

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number | string; icon: React.ComponentType<{ className?: string }>; color: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-slate-400">{label}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [tweetContent, setTweetContent] = useState('')
  const queryClient = useQueryClient()

  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: status } = useQuery({ queryKey: ['bot-status'], queryFn: getBotStatus })
  const { data: logs } = useQuery({ queryKey: ['tweet-logs'], queryFn: () => getTweetLogs(0, 10) })

  const sendMutation = useMutation({
    mutationFn: sendTweet,
    onSuccess: () => {
      toast.success('Tweet envoyé !')
      setTweetContent('')
      queryClient.invalidateQueries({ queryKey: ['tweet-logs'] })
    },
    onError: (err: Error) => toast.error(`Erreur: ${err.message}`),
  })

  const charsLeft = 280 - tweetContent.length

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          {profile?.name ? `@${profile.username}` : 'Connecté au Twitter Bot'}
        </p>
      </div>

      {/* Stats */}
      {profile?.metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Followers" value={profile.metrics.followers_count?.toLocaleString() ?? 0} icon={Twitter} color="bg-sky-500/10 text-sky-400" />
          <StatCard label="Following" value={profile.metrics.following_count?.toLocaleString() ?? 0} icon={Twitter} color="bg-purple-500/10 text-purple-400" />
          <StatCard label="Tweets postés" value={logs?.total ?? 0} icon={Send} color="bg-emerald-500/10 text-emerald-400" />
          <StatCard label="Jobs actifs" value={status?.jobs?.length ?? 0} icon={Repeat2} color="bg-orange-500/10 text-orange-400" />
        </div>
      )}

      {/* Compose */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">Envoyer un tweet</h2>
        <textarea
          className="input resize-none h-28"
          placeholder="Quoi de neuf ?"
          value={tweetContent}
          onChange={e => setTweetContent(e.target.value)}
          maxLength={280}
        />
        <div className="flex items-center justify-between">
          <span className={`text-sm ${charsLeft < 20 ? 'text-red-400' : 'text-slate-500'}`}>
            {charsLeft} caractères restants
          </span>
          <button
            className="btn-primary flex items-center gap-2"
            disabled={!tweetContent.trim() || sendMutation.isPending}
            onClick={() => sendMutation.mutate(tweetContent)}
          >
            <Send className="w-4 h-4" />
            {sendMutation.isPending ? 'Envoi...' : 'Tweeter'}
          </button>
        </div>
      </div>

      {/* Recent tweets */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">Tweets récents</h2>
        {logs?.logs?.length === 0 && (
          <p className="text-slate-500 text-sm">Aucun tweet pour l'instant.</p>
        )}
        <div className="space-y-3">
          {logs?.logs?.map((log: { id: number; content: string; sent_at: string; likes: number; retweets: number; impressions: number; replies: number; source: string }) => (
            <div key={log.id} className="border border-slate-800 rounded-lg p-4 space-y-2">
              <p className="text-sm text-slate-200">{log.content}</p>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>{formatDistanceToNow(new Date(log.sent_at), { addSuffix: true })}</span>
                <span className="badge bg-slate-800 text-slate-400">{log.source}</span>
                <span className="flex items-center gap-1"><Heart className="w-3 h-3" />{log.likes}</span>
                <span className="flex items-center gap-1"><Repeat2 className="w-3 h-3" />{log.retweets}</span>
                <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{log.impressions}</span>
                <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{log.replies}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
