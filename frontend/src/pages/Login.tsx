import { useState, type FormEvent } from 'react'
import { useAuth } from '../lib/auth'
import { Lock } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const [shaking, setShaking] = useState(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (login(password)) {
      setError(false)
    } else {
      setError(true)
      setShaking(true)
      setTimeout(() => setShaking(false), 500)
      setPassword('')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className={`card max-w-sm w-full ${shaking ? 'animate-shake' : ''}`}>
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-sky-500/10 flex items-center justify-center mb-4">
            <Lock className="w-7 h-7 text-sky-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">FlippX Panel</h1>
          <p className="text-slate-400 text-sm mt-1">Enter password to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(false) }}
              placeholder="Password"
              className={`input text-center text-lg tracking-wider ${error ? 'ring-2 ring-red-500 border-red-500' : ''}`}
              autoFocus
            />
            {error && (
              <p className="text-red-400 text-sm text-center mt-2">Wrong password</p>
            )}
          </div>
          <button type="submit" className="btn-primary w-full">
            Unlock
          </button>
        </form>
      </div>
    </div>
  )
}
