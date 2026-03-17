import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Trash2, ToggleLeft, ToggleRight, List, MessageSquare } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  getQueueTweets, addToQueue, removeFromQueue,
  getRules, createRule, toggleRule, deleteRule
} from '../lib/api'

export default function QueuePage() {
  const [tab, setTab] = useState<'queue' | 'rules'>('queue')
  const [queueContent, setQueueContent] = useState('')
  const [queuePriority, setQueuePriority] = useState(0)
  const [ruleKeyword, setRuleKeyword] = useState('')
  const [ruleTemplate, setRuleTemplate] = useState('')
  const [ruleMatchType, setRuleMatchType] = useState('contains')
  const queryClient = useQueryClient()

  const { data: queueData, isError: queueError, error: queueErr } = useQuery({ queryKey: ['queue'], queryFn: () => getQueueTweets('pending') })
  const { data: rules } = useQuery({ queryKey: ['rules'], queryFn: getRules })

  const addQueueMutation = useMutation({
    mutationFn: () => addToQueue(queueContent, queuePriority),
    onSuccess: () => {
      toast.success('Ajouté à la queue')
      setQueueContent('')
      queryClient.invalidateQueries({ queryKey: ['queue'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const removeQueueMutation = useMutation({
    mutationFn: removeFromQueue,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['queue'] }),
  })

  const createRuleMutation = useMutation({
    mutationFn: () => createRule({ keyword: ruleKeyword, reply_template: ruleTemplate, match_type: ruleMatchType }),
    onSuccess: () => {
      toast.success('Règle créée')
      setRuleKeyword('')
      setRuleTemplate('')
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const toggleRuleMutation = useMutation({
    mutationFn: toggleRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rules'] }),
  })

  const deleteRuleMutation = useMutation({
    mutationFn: deleteRule,
    onSuccess: () => {
      toast.success('Règle supprimée')
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  return (
    <div className="p-4 md:p-8 space-y-4 md:space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Queue & Auto-reply</h1>
        <p className="text-slate-400 mt-0.5 text-sm">File d'attente et réponses auto</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1">
        <button onClick={() => setTab('queue')} className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors flex-1 min-h-[44px] ${tab === 'queue' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}>
          <List className="w-4 h-4" /> Queue ({queueData?.total ?? 0})
        </button>
        <button onClick={() => setTab('rules')} className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors flex-1 min-h-[44px] ${tab === 'rules' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}>
          <MessageSquare className="w-4 h-4" /> Rules ({Array.isArray(rules) ? rules.length : 0})
        </button>
      </div>

      {tab === 'queue' && (
        <div className="space-y-4 md:space-y-6">
          {/* Add to queue */}
          <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
            <h2 className="font-semibold text-sm flex items-center gap-2"><Plus className="w-4 h-4" />Ajouter à la queue</h2>
            <textarea className="input resize-none h-20 text-sm" placeholder="Contenu du tweet..." value={queueContent} onChange={e => setQueueContent(e.target.value)} maxLength={280} />
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <label className="text-xs text-slate-400 block mb-1">Priorité (0-10)</label>
                <input type="number" className="input min-h-[44px] w-full" min={0} max={10} value={queuePriority} onChange={e => setQueuePriority(Number(e.target.value))} />
              </div>
              <button className="btn-primary min-h-[44px] shrink-0" disabled={!queueContent.trim() || addQueueMutation.isPending} onClick={() => addQueueMutation.mutate()}>
                Ajouter
              </button>
            </div>
          </div>

          {/* Queue list */}
          <div className="card !p-4 md:!p-6 space-y-3">
            <h2 className="font-semibold text-sm">En attente ({queueData?.total ?? 0})</h2>
            {queueError && <p className="text-red-400 text-sm">Erreur API: {(queueErr as Error)?.message}</p>}
            {!queueError && queueData?.tweets?.length === 0 && <p className="text-slate-500 text-sm">La queue est vide.</p>}
            {queueData?.tweets?.map((tweet: { id: number; content: string; priority: number; created_at: string }) => (
              <div key={tweet.id} className="flex items-start gap-2 md:gap-3 border border-slate-800 rounded-lg p-3">
                <span className="badge bg-sky-500/10 text-sky-400 shrink-0 mt-0.5">P{tweet.priority}</span>
                <p className="text-sm text-slate-200 flex-1 line-clamp-2">{tweet.content}</p>
                <button className="text-slate-500 hover:text-red-400 transition-colors shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center" onClick={() => removeQueueMutation.mutate(tweet.id)}>
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'rules' && (
        <div className="space-y-4 md:space-y-6">
          {/* Create rule */}
          <div className="card !p-4 md:!p-6 space-y-3 md:space-y-4">
            <h2 className="font-semibold text-sm flex items-center gap-2"><Plus className="w-4 h-4" />Nouvelle règle</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Mot-clé</label>
                <input className="input min-h-[44px]" placeholder="ex: aide, help..." value={ruleKeyword} onChange={e => setRuleKeyword(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Type</label>
                <select className="input min-h-[44px]" value={ruleMatchType} onChange={e => setRuleMatchType(e.target.value)}>
                  <option value="contains">Contient</option>
                  <option value="exact">Exact</option>
                  <option value="regex">Regex</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Réponse auto</label>
              <textarea className="input resize-none h-20 text-sm" placeholder="Réponse à envoyer..." value={ruleTemplate} onChange={e => setRuleTemplate(e.target.value)} maxLength={280} />
            </div>
            <button className="btn-primary min-h-[44px] w-full sm:w-auto" disabled={!ruleKeyword.trim() || !ruleTemplate.trim() || createRuleMutation.isPending} onClick={() => createRuleMutation.mutate()}>
              Créer la règle
            </button>
          </div>

          {/* Rules list */}
          <div className="card !p-4 md:!p-6 space-y-3">
            <h2 className="font-semibold text-sm">Règles actives</h2>
            {(!Array.isArray(rules) || rules.length === 0) && <p className="text-slate-500 text-sm">Aucune règle configurée.</p>}
            {Array.isArray(rules) && rules.map((rule: { id: number; keyword: string; reply_template: string; match_type: string; is_active: boolean; trigger_count: number }) => (
              <div key={rule.id} className={`border rounded-lg p-3 md:p-4 transition-opacity ${rule.is_active ? 'border-slate-700' : 'border-slate-800 opacity-50'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="badge bg-purple-500/10 text-purple-400">{rule.keyword}</span>
                      <span className="badge bg-slate-800 text-slate-400">{rule.match_type}</span>
                      <span className="text-xs text-slate-500">{rule.trigger_count}x</span>
                    </div>
                    <p className="text-sm text-slate-300 line-clamp-2">{rule.reply_template}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => toggleRuleMutation.mutate(rule.id)} className="text-slate-400 hover:text-sky-400 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center">
                      {rule.is_active ? <ToggleRight className="w-5 h-5 text-emerald-400" /> : <ToggleLeft className="w-5 h-5" />}
                    </button>
                    <button onClick={() => deleteRuleMutation.mutate(rule.id)} className="text-slate-500 hover:text-red-400 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
