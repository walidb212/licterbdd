interface AlertBannerProps {
  message: string
  gravityScore: number
}

export default function AlertBanner({ message, gravityScore }: AlertBannerProps) {
  return (
    <div className="relative flex items-center gap-3 px-4 py-3 rounded-xl border border-red-200 bg-red-50/60 mb-4 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-100/40 to-transparent animate-sweep pointer-events-none" />
      <span className="w-2 h-2 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.4)] animate-pulse" />
      <span className="text-[13px] font-semibold text-red-600">{message}</span>
      <span className="text-[12px] text-gray-500">
        Gravity Score : <strong className="text-red-600 text-sm">{gravityScore}</strong>/10
      </span>
      <span className="ml-auto bg-red-500 text-white text-[9px] font-extrabold tracking-wider px-2.5 py-1 rounded animate-pulse-live">
        LIVE
      </span>
    </div>
  )
}
