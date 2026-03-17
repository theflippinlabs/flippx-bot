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

  if (isLoading) return <div className="p-4 md:p-8 text-slate-400">Chargement...</div>
  if (isError) return <div className="p-4 md:p-8 text-red-400">Erreur: {(error as Error)?.message || 'Impossible de charger les settings'}</div>
  if (!form) return <div className="p-4 md:p-8 text-slate-400">Chargement...</div>

  const update = (key: keyof BotSettings, value: unknown) => {
    setForm(prev => prev ? { ...prev, [key]: value } : prev)
  }

  const save = () => {
    if (!form) return
    mutation.mutate(form)
  }

  return (
    <div className="p-4 md:p-8 space-y-4 md:space-y-6 max-w-4xl">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl md:text-2xl font-bold">Settings</h1>
          <p className="text-slate-400 mt-0.5 text-sm">Configure le bot</p>
        </div>
        <button className="btn-primary flex items-center gap-2 shrink-0 min-h-[44px]" onClick={save} disabled={mutation.isPending}>
          <Save className="w-4 h-4" />
          <span className="hidden sm:inline">{mutation.isPending ? 'Saving...' : 'Sauvegarder'}</span>
          <span className="sm:hidden">{mutation.isPending ? '...' : 'Save'}</span>
        </button>
      </div>

      {/* Bot On/Off */}
      <div className="card !p-4 md:!p-6">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Power className={`w-5 h-5 shrink-0 ${form.bot_enabled ? 'text-emerald-400' : 'text-red-400'}`} />
            <div className="min-w-0">
              <h2 className="font-semibold text-sm md:text-base">Bot {form.bot_enabled ? 'Actif' : 'Désactivé'}</h2>
              <p className="text-xs text-slate-400 truncate">Active/désactive les actions auto</p>
            </div>
          </div>
          <button
            onClick={() => update('bot_enabled', !form.bot_enabled)}
            className={`relative w-12 h-7 rounded-full transition-colors shrink-0 min-h-[44px] flex items-center ${form.bot_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${form.bot_enabled ? 'left-6' : 'left-1'}`} />
          </button>
        </div>
      </div>

      {/* Posting */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm md:text-base flex items-center gap-2"><Clock className="w-4 h-4 text-sky-400" /> Posting</h2>
        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Tweets / jour</label>
            <input type="number" className="input min-h-[44px]" min={1} max={50} value={form.tweets_per_day} onChange={e => update('tweets_per_day', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Intervalle (min)</label>
            <input type="number" className="input min-h-[44px]" min={10} max={1440} value={form.tweet_interval_minutes} onChange={e => update('tweet_interval_minutes', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Heure début</label>
            <input type="number" className="input min-h-[44px]" min={0} max={23} value={form.active_hours_start} onChange={e => update('active_hours_start', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Heure fin</label>
            <input type="number" className="input min-h-[44px]" min={0} max={23} value={form.active_hours_end} onChange={e => update('active_hours_end', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Engagement */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm md:text-base flex items-center gap-2"><Heart className="w-4 h-4 text-pink-400" /> Engagement</h2>
        <div className="flex items-center justify-between min-h-[44px]">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-slate-400" />
            <span className="text-sm">Auto-reply</span>
          </div>
          <button
            onClick={() => update('auto_reply_enabled', !form.auto_reply_enabled)}
            className={`relative w-12 h-7 rounded-full transition-colors shrink-0 ${form.auto_reply_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${form.auto_reply_enabled ? 'left-6' : 'left-1'}`} />
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2 md:gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Replies</label>
            <input type="number" className="input min-h-[44px]" min={0} max={20} value={form.max_replies_per_cycle} onChange={e => update('max_replies_per_cycle', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Likes</label>
            <input type="number" className="input min-h-[44px]" min={0} max={20} value={form.max_likes_per_cycle} onChange={e => update('max_likes_per_cycle', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Retweets</label>
            <input type="number" className="input min-h-[44px]" min={0} max={10} value={form.max_retweets_per_cycle} onChange={e => update('max_retweets_per_cycle', Number(e.target.value))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Min followers reply</label>
            <input type="number" className="input min-h-[44px]" min={0} value={form.min_followers_to_reply} onChange={e => update('min_followers_to_reply', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Min likes RT</label>
            <input type="number" className="input min-h-[44px]" min={0} value={form.min_likes_to_retweet} onChange={e => update('min_likes_to_retweet', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Human-like behavior */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm md:text-base flex items-center gap-2"><Shuffle className="w-4 h-4 text-yellow-400" /> Comportement humain</h2>
        <div className="grid grid-cols-3 gap-2 md:gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Skip %</label>
            <input type="number" className="input min-h-[44px]" min={0} max={100} value={form.random_skip_chance} onChange={e => update('random_skip_chance', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Délai min</label>
            <input type="number" className="input min-h-[44px]" min={0} max={60} value={form.min_delay_seconds} onChange={e => update('min_delay_seconds', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Délai max</label>
            <input type="number" className="input min-h-[44px]" min={1} max={120} value={form.max_delay_seconds} onChange={e => update('max_delay_seconds', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Queue */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm md:text-base flex items-center gap-2"><Repeat className="w-4 h-4 text-purple-400" /> Queue auto-refill</h2>
        <div className="flex items-center justify-between min-h-[44px]">
          <span className="text-sm">Auto-refill activé</span>
          <button
            onClick={() => update('auto_refill_enabled', !form.auto_refill_enabled)}
            className={`relative w-12 h-7 rounded-full transition-colors shrink-0 ${form.auto_refill_enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
          >
            <span className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${form.auto_refill_enabled ? 'left-6' : 'left-1'}`} />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Seuil refill</label>
            <input type="number" className="input min-h-[44px]" min={1} max={100} value={form.refill_threshold} onChange={e => update('refill_threshold', Number(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Nombre à générer</label>
            <input type="number" className="input min-h-[44px]" min={10} max={500} value={form.refill_count} onChange={e => update('refill_count', Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* Persona */}
      <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
        <h2 className="font-semibold text-sm md:text-base flex items-center gap-2"><Bot className="w-4 h-4 text-emerald-400" /> Persona</h2>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Persona des tweets</label>
          <textarea className="input resize-none h-28 md:h-24 text-sm min-h-[80px]" value={form.tweet_persona} onChange={e => update('tweet_persona', e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Persona des réponses</label>
          <textarea className="input resize-none h-28 md:h-24 text-sm min-h-[80px]" value={form.reply_persona} onChange={e => update('reply_persona', e.target.value)} />
        </div>
      </div>
    </div>
  )
}
