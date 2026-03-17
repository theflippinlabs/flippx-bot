import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { Save, Power, MessageSquare, Heart, Repeat, Clock, Bot, Shuffle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getSettings, updateSettings } from '../lib/api'

interface BotSettings {
  bot_enabled: boolean
  tweets_per_day: number
  tweet_interval_minutes: number
  active_hours_start: number
  active_hours_end: number
  auto_reply_enabled: boolean
  max_replies_per_cycle: number
  max_likes_per_cycle: number
  max_retweets_per_cycle: number
  min_followers_to_reply: number
  min_likes_to_retweet: number
  random_skip_chance: number
  min_delay_seconds: number
  max_delay_seconds: number
  auto_refill_enabled: boolean
  refill_threshold: number
  refill_count: number
  tweet_persona: string
  reply_persona: string
}

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading, isError, error } = useQuery<BotSettings>({
    queryKey: ['settings'],
    queryFn: getSettings,
  })

  const [form, setForm] = useState<BotSettings | null>(null)

  useEffect(() => {
    if (settings) setForm({ ...settings })
  }, [settings])

  const mutation = useMutation({
    mutationFn: (data: Partial<BotSettings>) => updateSettings(data),
    onSuccess: () => {
      toast.success('Settings saved')
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['bot-status'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  if (isLoading) return <div className="p-8 text-slate-400">Chargement...</div>
  if (isError) return <div className="p-8 text-red-400">Erreur: {(error as Error)?.message || 'Impossible de charger les settings'}</div>
  if (!form) return <div className="p-8 text-slate-400">Chargement...</div>

  const update = (key: keyof BotSettings, value: unknown) => {
    setForm(prev => prev ? { ...prev, [key]: value } : prev)
  }

  const save = () => {
    if (!form) return
    mutation.mutate(form)
  }

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-slate-400 mt-1">Configure le comportement du bot</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={save} disabled={mutation.isPending}>
          <Save className="w-4 h-4" />
          {mutation.isPending ? 'Saving...' : 'Sauvegarder'}
        </button>
      </div>

      {/* Bot On/Off */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Power className={`w-5 h-5 ${form.bot_enabled ? 'text-emerald-400' : 'text-red-400'}`} />
            <div>
              <h2 className="font-semibold">Bot {form.bot_enabled ? 'Actif' : 'Désactivé'}</h2>
              <p className="text-sm text-slate-400">Active/désactive toutes les actions automatiques</p>
            </div>
          </div>
          <button
            onClick={() => update('bot_enabled', !form.bot_enabled)}
            className={`relative w-12 h-6 rounded-full transition-colors ${form.bot_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${form.bot_enabled ? 'left-6' : 'left-0.5'}`} />
          </button>
        </div>
      </div>

      {/* Posting */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2"><Clock className="w-4 h-4 text-sky-400" /> Posting</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Tweets par jour (max)</label>
            <input type="number" className="input" min={1} max={50} value={form.tweets_per_day} onChange={e => update('tweets_per_day', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Intervalle min (minutes)</label>
            <input type="number" className="input" min={10} max={1440} value={form.tweet_interval_minutes} onChange={e => update('tweet_interval_minutes', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Heure début (0-23)</label>
            <input type="number" className="input" min={0} max={23} value={form.active_hours_start} onChange={e => update('active_hours_start', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Heure fin (0-23)</label>
            <input type="number" className="input" min={0} max={23} value={form.active_hours_end} onChange={e => update('active_hours_end', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Engagement */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2"><Heart className="w-4 h-4 text-pink-400" /> Engagement</h2>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-slate-400" />
            <span className="text-sm">Auto-reply</span>
          </div>
          <button
            onClick={() => update('auto_reply_enabled', !form.auto_reply_enabled)}
            className={`relative w-12 h-6 rounded-full transition-colors ${form.auto_reply_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${form.auto_reply_enabled ? 'left-6' : 'left-0.5'}`} />
          </button>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Replies / cycle</label>
            <input type="number" className="input" min={0} max={20} value={form.max_replies_per_cycle} onChange={e => update('max_replies_per_cycle', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Likes / cycle</label>
            <input type="number" className="input" min={0} max={20} value={form.max_likes_per_cycle} onChange={e => update('max_likes_per_cycle', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Retweets / cycle</label>
            <input type="number" className="input" min={0} max={10} value={form.max_retweets_per_cycle} onChange={e => update('max_retweets_per_cycle', Number(e.target.value))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Min followers pour reply</label>
            <input type="number" className="input" min={0} value={form.min_followers_to_reply} onChange={e => update('min_followers_to_reply', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Min likes pour RT</label>
            <input type="number" className="input" min={0} value={form.min_likes_to_retweet} onChange={e => update('min_likes_to_retweet', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Human-like behavior */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2"><Shuffle className="w-4 h-4 text-yellow-400" /> Comportement humain</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Skip aléatoire (%)</label>
            <input type="number" className="input" min={0} max={100} value={form.random_skip_chance} onChange={e => update('random_skip_chance', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Délai min (sec)</label>
            <input type="number" className="input" min={0} max={60} value={form.min_delay_seconds} onChange={e => update('min_delay_seconds', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Délai max (sec)</label>
            <input type="number" className="input" min={1} max={120} value={form.max_delay_seconds} onChange={e => update('max_delay_seconds', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Queue */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2"><Repeat className="w-4 h-4 text-purple-400" /> Queue auto-refill</h2>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm">Auto-refill activé</span>
          <button
            onClick={() => update('auto_refill_enabled', !form.auto_refill_enabled)}
            className={`relative w-12 h-6 rounded-full transition-colors ${form.auto_refill_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${form.auto_refill_enabled ? 'left-6' : 'left-0.5'}`} />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Seuil de refill</label>
            <input type="number" className="input" min={1} max={100} value={form.refill_threshold} onChange={e => update('refill_threshold', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Nombre à générer</label>
            <input type="number" className="input" min={10} max={500} value={form.refill_count} onChange={e => update('refill_count', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Persona */}
      <div className="card space-y-4">
        <h2 className="font-semibold flex items-center gap-2"><Bot className="w-4 h-4 text-emerald-400" /> Persona</h2>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Persona des tweets</label>
          <textarea className="input resize-none h-24" value={form.tweet_persona} onChange={e => update('tweet_persona', e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Persona des réponses</label>
          <textarea className="input resize-none h-24" value={form.reply_persona} onChange={e => update('reply_persona', e.target.value)} />
        </div>
      </div>
    </div>
  )
}
