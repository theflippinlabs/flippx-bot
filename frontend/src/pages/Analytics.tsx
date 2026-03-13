import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import { Heart, Repeat2, Eye, TrendingUp, MessageCircle } from 'lucide-react'
import { getOverview, getTimeline, getTopTweets } from '../lib/api'

function MetricCard({ label, value, icon: Icon, color, sub }: { label: string; value: string | number; icon: React.ComponentType<{ className?: string }>; color: string; sub?: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-sm">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className="text-3xl font-bold">{typeof value === 'number' ? value.toLocaleString() : value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(7)
  const [topMetric, setTopMetric] = useState('likes')

  const { data: overview } = useQuery({ queryKey: ['analytics-overview'], queryFn: getOverview })
  const { data: timeline } = useQuery({ queryKey: ['analytics-timeline', days], queryFn: () => getTimeline(days) })
  const { data: topTweets } = useQuery({ queryKey: ['top-tweets', topMetric], queryFn: () => getTopTweets(topMetric) })

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-slate-400 mt-1">Performance de tes tweets</p>
      </div>

      {/* Overview cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Total tweets" value={overview?.total_tweets ?? 0} icon={TrendingUp} color="text-sky-400" />
        <MetricCard label="Total likes" value={overview?.total_likes ?? 0} icon={Heart} color="text-pink-400" />
        <MetricCard label="Total retweets" value={overview?.total_retweets ?? 0} icon={Repeat2} color="text-emerald-400" />
        <MetricCard label="Impressions" value={overview?.total_impressions ?? 0} icon={Eye} color="text-purple-400" sub={`${overview?.engagement_rate ?? 0}% engagement`} />
      </div>

      {/* Timeline chart */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Évolution sur {days} jours</h2>
          <div className="flex gap-2">
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setDays(d)} className={`text-sm px-3 py-1 rounded-lg transition-colors ${days === d ? 'bg-sky-500/20 text-sky-400' : 'text-slate-400 hover:text-white'}`}>
                {d}j
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={timeline ?? []}>
            <defs>
              <linearGradient id="colorLikes" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ec4899" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorImpressions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 12 }} />
            <YAxis stroke="#475569" tick={{ fontSize: 12 }} />
            <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }} />
            <Legend />
            <Area type="monotone" dataKey="likes" stroke="#ec4899" fill="url(#colorLikes)" strokeWidth={2} />
            <Area type="monotone" dataKey="impressions" stroke="#a855f7" fill="url(#colorImpressions)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Top tweets */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Top tweets</h2>
          <select className="input w-40" value={topMetric} onChange={e => setTopMetric(e.target.value)}>
            <option value="likes">Par likes</option>
            <option value="retweets">Par retweets</option>
            <option value="impressions">Par impressions</option>
          </select>
        </div>
        {!topTweets?.length && <p className="text-slate-500 text-sm">Aucune donnée disponible.</p>}
        <div className="space-y-3">
          {topTweets?.map((tweet: { id: number; content: string; likes: number; retweets: number; impressions: number; replies: number }, i: number) => (
            <div key={tweet.id} className="flex items-start gap-3 border border-slate-800 rounded-lg p-4">
              <span className="text-2xl font-bold text-slate-700 w-8">#{i + 1}</span>
              <div className="flex-1 space-y-2">
                <p className="text-sm text-slate-200">{tweet.content}</p>
                <div className="flex gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1 text-pink-400"><Heart className="w-3 h-3" />{tweet.likes}</span>
                  <span className="flex items-center gap-1 text-emerald-400"><Repeat2 className="w-3 h-3" />{tweet.retweets}</span>
                  <span className="flex items-center gap-1 text-purple-400"><Eye className="w-3 h-3" />{tweet.impressions}</span>
                  <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" />{tweet.replies}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
