import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import Layout from './components/Layout'
import LoginPage from './pages/Login'
import Dashboard from './pages/Dashboard'
import SchedulerPage from './pages/Scheduler'
import QueuePage from './pages/Queue'
import LibraryPage from './pages/Library'
import AnalyticsPage from './pages/Analytics'
import SettingsPage from './pages/Settings'

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="scheduler" element={<SchedulerPage />} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ProtectedRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
