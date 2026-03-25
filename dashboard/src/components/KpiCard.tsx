interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  variant?: 'default' | 'danger' | 'success' | 'warning'
  delta?: number
  deltaLabel?: string
}

const VALUE_COLORS = {
  default: 'text-gray-900',
  danger: 'text-red-500',
  success: 'text-green-600',
  warning: 'text-amber-500',
}

const BORDER_COLORS = {
  default: '',
  danger: 'ring-1 ring-red-100',
  success: '',
  warning: '',
}

export default function KpiCard({ label, value, sub, variant = 'default', delta, deltaLabel }: KpiCardProps) {
  return (
    <div className={`bg-white rounded-[16px] shadow-[0_2px_8px_rgba(0,0,0,0.06)] px-5 py-4 transition-all hover:shadow-[0_8px_24px_rgba(0,0,0,0.1)] hover:-translate-y-0.5 ${BORDER_COLORS[variant]}`}>
      <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">{label}</div>
      <div className="flex items-baseline gap-2">
        <div className={`text-[26px] font-bold leading-none tracking-tight ${VALUE_COLORS[variant]}`}>{value}</div>
        {delta != null && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full
            ${delta > 0 ? 'text-green-600 bg-green-50' : delta < 0 ? 'text-red-500 bg-red-50' : 'text-gray-400 bg-gray-100'}`}>
            {delta > 0 ? '+' : ''}{deltaLabel ?? (delta + '%')}
          </span>
        )}
      </div>
      {delta == null && sub && <div className="text-[11px] text-gray-400 mt-2">{sub}</div>}
    </div>
  )
}
