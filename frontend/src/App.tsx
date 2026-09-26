import { useEffect, useState } from 'react'
import { api, getErrorMessage } from './api/client.ts'
import AuditPanel from './components/AuditPanel.tsx'
import AuthPanel from './components/AuthPanel.tsx'
import ControlsPanel from './components/ControlsPanel.tsx'
import {
  PageHeader,
  RequestErrorBanner,
  SiteNav,
} from './components/PageChrome.tsx'
import QueryPanel from './components/QueryPanel.tsx'
import { API_PATHS, ROUTES, TEXT } from './constants.ts'
import type {
  AnswerResponse,
  AuditEvent,
  AuditResponse,
  AuthSubmission,
  HealthResponse,
  MeResponse,
  User,
} from './types.ts'

export default function App() {
  const isLoginPage = window.location.pathname === ROUTES.login
  const [user, setUser] = useState<User | null>(null)
  const [requestError, setRequestError] = useState('')
  const [answer, setAnswer] = useState<AnswerResponse | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [policy, setPolicy] = useState(TEXT.policyLoading)
  const [busy, setBusy] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)

  const loadAudit = async (account: User | null) => {
    if (!account || !['hr_payroll', 'hr_partner'].includes(account.role)) {
      setEvents([])
      return
    }
    try {
      const data = await api<AuditResponse>(API_PATHS.audit)
      setEvents(data.events ?? [])
    } catch (error) {
      setEvents([])
      setRequestError(getErrorMessage(error))
    }
  }

  const submitAuth = async ({
    registering,
    userId,
    fullName,
    password,
  }: AuthSubmission) => {
    setBusy(true)
    setRequestError('')
    try {
      const path = registering ? API_PATHS.register : API_PATHS.login
      const body = registering
        ? { username: userId, name: fullName, password }
        : { userId, password }
      await api(path, { method: 'POST', body: JSON.stringify(body) })
      window.location.replace(ROUTES.home)
    } finally {
      setBusy(false)
    }
  }

  const signOut = async () => {
    setBusy(true)
    setRequestError('')
    try {
      await api(API_PATHS.logout, { method: 'POST', body: '{}' })
      window.location.replace(ROUTES.login)
    } catch (error) {
      setRequestError(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  const ask = async (question: string) => {
    if (!user) return
    setBusy(true)
    setRequestError('')
    setAnswer(null)
    try {
      const data = await api<AnswerResponse>(API_PATHS.ask, {
        method: 'POST',
        body: JSON.stringify({ question }),
      })
      setAnswer(data)
      await loadAudit(user)
    } catch (error) {
      setRequestError(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    api<HealthResponse>(API_PATHS.health)
      .then((data) => setPolicy(data.policyVersion))
      .catch((error) => {
        setPolicy(TEXT.serviceUnavailable)
        setRequestError(getErrorMessage(error))
      })
    api<MeResponse>(API_PATHS.me)
      .then((data) => {
        if (!data.user && !isLoginPage) {
          window.location.replace(ROUTES.login)
          return
        }
        if (data.user && isLoginPage) {
          window.location.replace(ROUTES.home)
          return
        }
        setUser(data.user)
        loadAudit(data.user)
      })
      .catch((error) => setRequestError(getErrorMessage(error)))
      .finally(() => setAuthChecked(true))
  }, [])

  return (
    <main>
      <SiteNav policy={policy} />
      <RequestErrorBanner
        message={requestError}
        onDismiss={() => setRequestError('')}
      />
      {(isLoginPage || authChecked) && (
        <>
          <PageHeader isLoginPage={isLoginPage} />
          <AuthPanel
            user={user}
            busy={busy}
            onSubmitAuth={submitAuth}
            onSignOut={signOut}
          />
          {!isLoginPage && user && (
            <>
              <section className="grid">
                <QueryPanel
                  user={user}
                  busy={busy}
                  answer={answer}
                  onAsk={ask}
                />
                <ControlsPanel />
              </section>
              <AuditPanel events={events} />
            </>
          )}
          <footer>{TEXT.footer}</footer>
        </>
      )}
    </main>
  )
}
