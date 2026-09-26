import { useState } from 'react'
import type { FormEvent } from 'react'
import { getErrorMessage } from '../api/client.ts'
import { TEXT } from '../constants.ts'
import type { AuthSubmission, User } from '../types.ts'

interface AuthPanelProps {
  user: User | null
  busy: boolean
  onSubmitAuth: (submission: AuthSubmission) => Promise<void>
  onSignOut: () => Promise<void>
}

export default function AuthPanel({
  user,
  busy,
  onSubmitAuth,
  onSignOut,
}: AuthPanelProps) {
  const [authMode, setAuthMode] = useState('signin')
  const [userId, setUserId] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const registering = authMode === 'register'

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (registering && password !== confirmPassword) {
      setLoginError(TEXT.errors.passwordsMismatch)
      return
    }
    setLoginError('')
    try {
      await onSubmitAuth({ registering, userId, fullName, password })
    } catch (error) {
      setLoginError(getErrorMessage(error))
    }
  }

  const toggleMode = () => {
    setAuthMode(registering ? 'signin' : 'register')
    setUserId('')
    setPassword('')
    setConfirmPassword('')
    setLoginError('')
  }

  return (
    <section className="identity">
      {user ? (
        <>
          <div>
            <b>{TEXT.home.signedInAs(user.name)}</b>
            <small>
              {user.loginName
                ? TEXT.home.registeredAccount(user.loginName)
                : user.label}
            </small>
          </div>
          <button onClick={onSignOut} disabled={busy}>
            {TEXT.home.signOut}
          </button>
        </>
      ) : (
        <form onSubmit={submit}>
          <div>
            <b>
              {registering
                ? TEXT.login.registerHeading
                : TEXT.login.signInHeading}
            </b>
            <small>
              {registering
                ? TEXT.login.registerDescription
                : TEXT.login.signInDescription}
            </small>
          </div>
          <input
            aria-label={registering ? TEXT.login.username : TEXT.login.userId}
            autoComplete="username"
            placeholder={registering ? TEXT.login.username : TEXT.login.userId}
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            required
            minLength={registering ? 3 : undefined}
            maxLength={registering ? 32 : undefined}
          />
          {registering && (
            <input
              aria-label={TEXT.login.fullName}
              autoComplete="name"
              placeholder={TEXT.login.fullName}
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              required
              maxLength={120}
            />
          )}
          <input
            aria-label={TEXT.login.password}
            autoComplete={registering ? 'new-password' : 'current-password'}
            type="password"
            placeholder={TEXT.login.password}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={registering ? 8 : undefined}
          />
          {registering && (
            <input
              aria-label={TEXT.login.confirmPassword}
              autoComplete="new-password"
              type="password"
              placeholder={TEXT.login.confirmPassword}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
          )}
          <button type="submit" disabled={busy}>
            {busy
              ? TEXT.login.pleaseWait
              : registering
                ? TEXT.login.createAccount
                : TEXT.login.signInHeading}
          </button>
          <button
            type="button"
            className="authToggle"
            disabled={busy}
            onClick={toggleMode}
          >
            {registering ? TEXT.login.existingAccount : TEXT.login.newAccount}
          </button>
          {loginError && (
            <p className="loginError" role="alert">
              {loginError}
            </p>
          )}
        </form>
      )}
    </section>
  )
}
