import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || ''

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

// Auth
export const getProfile = () => api.get('/auth/me').then(r => r.data)
export const getBotStatus = () => api.get('/auth/status').then(r => r.data)

// Tweets
export const sendTweet = (content: string) =>
  api.post('/tweets/send', { content }).then(r => r.data)
export const getTweetLogs = (skip = 0, limit = 50) =>
  api.get('/tweets/logs', { params: { skip, limit } }).then(r => r.data)

// Scheduler
export const getScheduledTweets = (status?: string) =>
  api.get('/scheduler/', { params: { status } }).then(r => r.data)
export const createScheduledTweet = (content: string, scheduled_at: string) =>
  api.post('/scheduler/', { content, scheduled_at }).then(r => r.data)
export const cancelScheduledTweet = (id: number) =>
  api.delete(`/scheduler/${id}`).then(r => r.data)

// Queue
export const getQueueTweets = (status = 'pending') =>
  api.get('/queue/tweets', { params: { status } }).then(r => r.data)
export const addToQueue = (content: string, priority = 0) =>
  api.post('/queue/tweets', { content, priority }).then(r => r.data)
export const removeFromQueue = (id: number) =>
  api.delete(`/queue/tweets/${id}`).then(r => r.data)

// Library (all tweets, all statuses)
export const getLibrary = (status?: string, skip = 0, limit = 100) =>
  api.get('/queue/library', { params: { status: status || undefined, skip, limit } }).then(r => r.data)
export const deleteTweet = (id: number) =>
  api.delete(`/queue/tweets/${id}`).then(r => r.data)

// Auto-reply rules
export const getRules = () => api.get('/queue/rules').then(r => r.data)
export const createRule = (data: { keyword: string; reply_template: string; match_type: string }) =>
  api.post('/queue/rules', data).then(r => r.data)
export const toggleRule = (id: number) =>
  api.patch(`/queue/rules/${id}/toggle`).then(r => r.data)
export const deleteRule = (id: number) =>
  api.delete(`/queue/rules/${id}`).then(r => r.data)

// Analytics
export const getOverview = () => api.get('/analytics/overview').then(r => r.data)
export const getTimeline = (days = 7) =>
  api.get('/analytics/timeline', { params: { days } }).then(r => r.data)
export const getTopTweets = (metric = 'likes') =>
  api.get('/analytics/top-tweets', { params: { metric } }).then(r => r.data)

// Bot control
export const toggleBot = () => api.post('/auth/toggle').then(r => r.data)
export const triggerBotCycle = () => api.post('/auth/run-cycle').then(r => r.data)

// Settings
export const getSettings = () => api.get('/settings/').then(r => r.data)
export const updateSettings = (data: {
  tweet_interval_minutes?: number
  replies_per_run?: number
  likes_per_run?: number
  retweets_per_run?: number
}) => api.patch('/settings/', data).then(r => r.data)
export const getPersona = () => api.get('/settings/persona').then(r => r.data)
export const updatePersona = (data: {
  bot_persona?: string
  reply_persona?: string
}) => api.patch('/settings/persona', data).then(r => r.data)

// Activity
export const getActivityLog = (limit = 50) =>
  api.get('/activity/', { params: { limit } }).then(r => r.data)
