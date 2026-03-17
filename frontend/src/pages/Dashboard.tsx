import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Send, Heart, Repeat2, MessageCircle, Zap, Power,
  Play, Clock, TrendingUp,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  getProfile, getBotStatus, sendTweet, toggleBot,
  triggerBotCycle, getActivityLog,
} from '../lib/api'
import { formatDistanceToNow } from 'date-fns'

const activityIcons: Record<string, { icon: typeof Heart; color: string }> = {
  posted: { icon: Send, color: 'text-sky-400 bg-sky-400/10' },
  replied: { icon: MessageCircle, color: 'text-purple-400 bg-purple-400/10' },
  liked: { icon: Heart, color: 'text-pink-400 bg-pink-400/10' },
  retweeted: { icon: Repeat2, color: 'text-emerald-400 bg-emerald-400/10' },
}

export default function Dashboard() {
  const [tweetContent, setTweetContent] = useState('')
  const queryClient = useQueryClient()

  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const { data: status } = useQuery({
    queryKey: ['bot-status'],
    queryFn: getBotStatus,
    refetchInterval: 15_000,
  })
  const { data: activityData } = useQuery({
    queryKey: ['activity'],
    queryFn: () => getActivityLog(50),
    refetchInterval: 30_000,
  })

  const toggleMutation = useMutation({
    mutationFn: toggleBot,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bot-status'] })
      toast.success(data.bot_enabled ? 'Bot started' : 'Bot stopped')
    },
    onError: () => toast.error('Failed to toggle bot'),
  })

  const cycleMutation = useMutation({
    mutationFn: triggerBotCycle,
    onSuccess: () => {
      toast.success('Bot cycle triggered!')
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['activity'] })
      }, 10_000)
    },
    onError: () => toast.error('Failed to trigger cycle'),
  })

  const sendMutation = useMutation({
    mutationFn: sendTweet,
    onSuccess: () => {
      toast.success('Tweet sent!')
      setTweetContent('')
      queryClient.invalidateQueries({ queryKey: ['activity'] })
    },
    onError: (err: Error) => toast.error(`Error: ${err.message}`),
  })

  const stats = activityData?.stats
  const activity = activityData?.activity ?? []
  const charsLeft = 280 - tweetContent.length

  return (
    <div className="p-4 md:p-8 space-y-5 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold">Dashboard</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {profile?.name ? `@${profile.username}` : 'FlippX Bot'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status?.bot_enabled && (
            <Zap className="w-4 h-4 text-yellow-400" />
          )}
        </div>
      </div>

      {/* Bot Control Card */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              status?.bot_enabled ? 'bg-emerald-500/10' : 'bg-slate-800'
            }`}>
              <Power className={`w-5 h-5 ${status?.bot_enabled ? 'text-emerald-400' : 'text-slate-500'}`} />
            </div>
            <div>
              <p className="font-semibold text-sm">
                Bot {status?.bot_enabled ? 'Running' : 'Stopped'}
              </p>
              <p className="text-xs text-slate-500">
                {status?.jobs?.length ?? 0} active jobs
              </p>
            </div>
          </div>
          <button
            onClick={() => toggleMutation.mutate()}
            disabled={toggleMutation.isPending}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              status?.bot_enabled
                ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
            }`}
          >
            {status?.bot_enabled ? 'Stop' : 'Start'}
          </button>
        </div>

        <button
          onClick={() => cycleMutation.mutate()}
          disabled={cycleMutation.isPending}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-sky-500/10 text-sky-400 hover:bg-sky-500/20 text-sm font-medium transition-colors"
        >
          <Play className="w-4 h-4" />
          {cycleMutation.isPending ? 'Running cycle...' : 'Run Cycle Now'}
        </button>
      </div>

      {/* Stats — same data as Analytics/Stats page */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Tweets" value={stats?.total_tweets ?? 0} icon={Send} color="bg-sky-400/10 text-sky-400" />
        <StatCard label="Today" value={stats?.tweets_today ?? 0} icon={Clock} color="bg-purple-400/10 text-purple-400" />
        <StatCard label="Likes" value={stats?.total_likes ?? 0} icon={Heart} color="bg-pink-400/10 text-pink-400" />
        <StatCard label="Impressions" value={stats?.total_impressions ?? 0} icon={TrendingUp} color="bg-emerald-400/10 text-emerald-400" />
      </div>

      {/* Quick Compose */}
      <div className="card space-y-3">
        <h2 className="font-semibold text-sm flex items-center gap-2">
          <Send className="w-4 h-4 text-sky-400" />
          Quick Tweet
        </h2>
        <textarea
          className="input resize-none h-20 text-sm"
          placeholder="What's happening?"
          value={tweetContent}
          onChange={e => setTweetContent(e.target.value)}
          maxLength={280}
        />
        <div className="flex items-center justify-between">
          <span className={`text-xs ${charsLeft < 20 ? 'text-red-400' : 'text-slate-500'}`}>
            {charsLeft}
          </span>
          <button
            className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
            disabled={!tweetContent.trim() || sendMutation.isPending}
            onClick={() => sendMutation.mutate(tweetContent)}
          >
            <Send className="w-3.5 h-3.5" />
            {sendMutation.isPending ? 'Sending...' : 'Tweet'}
          </button>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-sky-400" />
            Recent Activity
          </h2>
          <span className="text-xs text-slate-500">
            <Clock className="w-3 h-3 inline mr-1" />
            Auto-refresh
          </span>
        </div>

        {activity.length === 0 && (
          <p className="text-slate-500 text-sm py-4 text-center">No activity yet. Start the bot to see actions here.</p>
        )}

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {activity.slice(0, 30).map((item: {
            id: number
            content: string
            source: string
            tweet_id: string
            sent_at: string
            likes: number
            retweets: number
            impressions: number
            replies: number
          }) => {
            const config = activityIcons.posted
            const Icon = config.icon
            return (
              <div key={item.id} className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${config.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-300">Posted</span>
                    {item.source && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">{item.source}</span>
                    )}
                    {item.impressions > 0 && (
                      <span className="text-[10px] text-slate-500">{item.impressions} views</span>
                    )}
                  </div>
                  {item.content && (
                    <p className="text-xs text-slate-400 mt-0.5 truncate">{item.content}</p>
                  )}
                  <p className="text-[10px] text-slate-600 mt-1">
                    {item.sent_at ? formatDistanceToNow(new Date(item.sent_at), { addSuffix: true }) : ''}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, icon: Icon, color }: {
  label: string
  value: number | string
  icon: React.ComponentType<{ className?: string }>
  color: string
}) {
  return (
    <div className="card flex items-center gap-3 py-3 px-4">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <p className="text-lg font-bold">{value}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  )
}
