import { ROUTES, TEXT } from '../constants.ts'

export function SiteNav({
  policy,
  signedIn = false,
}: {
  policy: string
  signedIn?: boolean
}) {
  return (
    <nav>
      <div className="brand">
        <i>{TEXT.brandSymbol}</i> {TEXT.brandName}{' '}
        <span>{TEXT.brandTagline}</span>
      </div>
      <div className="navLinks">
        {signedIn && (
          <>
            <a
              href={ROUTES.home}
              aria-current={
                window.location.pathname === ROUTES.home ? 'page' : undefined
              }
            >
              Ask
            </a>
            <a
              href={ROUTES.upload}
              aria-current={
                window.location.pathname === ROUTES.upload ? 'page' : undefined
              }
            >
              Upload
            </a>
          </>
        )}
        <div className="policy">{policy}</div>
      </div>
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

export function PageHeader({
  isLoginPage,
  isUploadPage = false,
}: {
  isLoginPage: boolean
  isUploadPage?: boolean
}) {
  if (isUploadPage) {
    return (
      <header>
        <p className="kicker">YOUR PRIVATE KNOWLEDGE</p>
        <h1>Upload your documents.</h1>
        <p>
          Add a document to your private knowledge collection, then ask
          questions with answers grounded in its content.
        </p>
      </header>
    )
  }
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
