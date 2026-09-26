import { TEXT } from '../constants.ts'

export function SiteNav({ policy }: { policy: string }) {
  return (
    <nav>
      <div className="brand">
        <i>{TEXT.brandSymbol}</i> {TEXT.brandName}{' '}
        <span>{TEXT.brandTagline}</span>
      </div>
      <div className="policy">{policy}</div>
    </nav>
  )
}

interface RequestErrorBannerProps {
  message: string
  onDismiss: () => void
}

export function RequestErrorBanner({
  message,
  onDismiss,
}: RequestErrorBannerProps) {
  if (!message) return null

  return (
    <div className="requestError" role="alert">
      <span>{message}</span>
      <button type="button" aria-label={TEXT.dismissError} onClick={onDismiss}>
        {TEXT.dismissSymbol}
      </button>
    </div>
  )
}

export function PageHeader({ isLoginPage }: { isLoginPage: boolean }) {
  if (isLoginPage) {
    return (
      <header>
        <p className="kicker">{TEXT.login.kicker}</p>
        <h1>{TEXT.login.heading}</h1>
        <p>{TEXT.login.description}</p>
      </header>
    )
  }

  return (
    <header>
      <p className="kicker">{TEXT.home.kicker}</p>
      <h1>
        {TEXT.home.headingBeforeBreak}
        <br />
        {TEXT.home.headingAfterBreak} <em>{TEXT.home.headingEmphasis}</em>
      </h1>
      <p>{TEXT.home.description}</p>
    </header>
  )
}
