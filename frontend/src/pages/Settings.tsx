import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, User, Sliders, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { getSettings, updateSettings, getPersona, updatePersona } from '../lib/api'

export default function SettingsPage() {
  return (
    <div className="p-4 md:p-8 space-y-5 max-w-3xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-sky-400" />
          Settings
        </h1>
        <p className="text-slate-400 text-sm mt-0.5">Configure your FlippX bot</p>
      </div>

      <PersonaEditor />
      <BotParameters />
    </div>
  )
}

function PersonaEditor() {
  const queryClient = useQueryClient()
  const { data: persona } = useQuery({ queryKey: ['persona'], queryFn: getPersona })
  const [botPersona, setBotPersona] = useState('')
  const [replyPersona, setReplyPersona] = useState('')

  useEffect(() => {
    if (persona) {
      setBotPersona(persona.bot_persona ?? '')
      setReplyPersona(persona.reply_persona ?? '')
    }
  }, [persona])

  const mutation = useMutation({
    mutationFn: updatePersona,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persona'] })
      toast.success('Persona updated!')
    },
    onError: () => toast.error('Failed to update persona'),
  })

  const handleSave = () => {
    mutation.mutate({
      bot_persona: botPersona,
      reply_persona: replyPersona,
    })
  }

  return (
    <div className="card space-y-4">
      <h2 className="font-semibold text-sm flex items-center gap-2">
        <User className="w-4 h-4 text-sky-400" />
        Bot Persona
      </h2>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-slate-400 block mb-1.5">Tweet Persona</label>
          <textarea
            className="input resize-none h-28 text-sm"
            value={botPersona}
            onChange={e => setBotPersona(e.target.value)}
            placeholder="Describe how the bot should tweet..."
          />
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1.5">Reply Persona</label>
          <textarea
            className="input resize-none h-28 text-sm"
            value={replyPersona}
            onChange={e => setReplyPersona(e.target.value)}
            placeholder="Describe how the bot should reply..."
          />
        </div>

        <button
          onClick={handleSave}
          disabled={mutation.isPending}
          className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
        >
          <Save className="w-3.5 h-3.5" />
          {mutation.isPending ? 'Saving...' : 'Save Persona'}
        </button>
      </div>
    </div>
  )
}

function BotParameters() {
  const queryClient = useQueryClient()
  const { data: settings } = useQuery({ queryKey: ['settings'], queryFn: getSettings })
  const [interval, setInterval_] = useState(60)
  const [replies, setReplies] = useState(3)
  const [likes, setLikes] = useState(5)
  const [retweets, setRetweets] = useState(1)

  useEffect(() => {
    if (settings) {
      setInterval_(settings.tweet_interval_minutes ?? 60)
      setReplies(settings.replies_per_run ?? 3)
      setLikes(settings.likes_per_run ?? 5)
      setRetweets(settings.retweets_per_run ?? 1)
    }
  }, [settings])

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('Settings updated!')
    },
    onError: () => toast.error('Failed to update settings'),
  })

  const handleSave = () => {
    mutation.mutate({
      tweet_interval_minutes: interval,
      replies_per_run: replies,
      likes_per_run: likes,
      retweets_per_run: retweets,
    })
  }

  return (
    <div className="card space-y-4">
      <h2 className="font-semibold text-sm flex items-center gap-2">
        <Sliders className="w-4 h-4 text-sky-400" />
        Bot Parameters
      </h2>

      <div className="grid grid-cols-2 gap-3">
        <NumberField
          label="Cycle interval (min)"
          value={interval}
          onChange={setInterval_}
          min={5}
          max={1440}
        />
        <NumberField
          label="Replies per run"
          value={replies}
          onChange={setReplies}
          min={0}
          max={20}
        />
        <NumberField
          label="Likes per run"
          value={likes}
          onChange={setLikes}
          min={0}
          max={50}
        />
        <NumberField
          label="Retweets per run"
          value={retweets}
          onChange={setRetweets}
          min={0}
          max={10}
        />
      </div>

      <button
        onClick={handleSave}
        disabled={mutation.isPending}
        className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
      >
        <Save className="w-3.5 h-3.5" />
        {mutation.isPending ? 'Saving...' : 'Save Settings'}
      </button>
    </div>
  )
}

function NumberField({ label, value, onChange, min, max }: {
  label: string
  value: number
  onChange: (v: number) => void
  min: number
  max: number
}) {
  return (
    <div>
      <label className="text-xs text-slate-400 block mb-1.5">{label}</label>
      <input
        type="number"
        className="input text-sm"
        value={value}
        onChange={e => {
          const v = parseInt(e.target.value) || min
          onChange(Math.max(min, Math.min(max, v)))
        }}
        min={min}
        max={max}
      />
    </div>
  )
}
