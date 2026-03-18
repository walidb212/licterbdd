interface AlertBannerProps {
  message: string
  gravityScore: number
}

export default function AlertBanner({ message, gravityScore }: AlertBannerProps) {
  return (
    <div className="alert-banner" role="alert" aria-live="assertive">
      <div className="alert-banner__dot" />
      <span className="alert-banner__text">{message}</span>
      <span className="alert-banner__score">Gravity Score : {gravityScore}/10</span>
    </div>
  )
}
