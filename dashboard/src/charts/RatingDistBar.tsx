interface Props {
  data: { stars: number; count: number; pct: number }[]
}

const STAR_COLORS: Record<number, string> = {
  1: '#f43f5e', // rose-500
  2: '#f97316', // orange-500
  3: '#f59e0b', // amber-500
  4: '#3b82f6', // blue-500
  5: '#10b981', // emerald-500
}

export default function RatingDistBar({ data }: Props) {
  const barData = [...data].sort((a, b) => b.stars - a.stars);

  return (
    <div className="space-y-4 pt-2">
      {barData.map((d) => (
        <div key={d.stars} className="flex items-center gap-3 transition-all hover:translate-x-1 group">
          <div className="w-6 text-[11px] font-bold text-gray-500">{d.stars}★</div>
          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden relative">
            <div 
              className="h-full rounded-full shadow-[0_1px_3px_rgba(0,0,0,0.1)] transition-all duration-1000 ease-out" 
              style={{ 
                width: `${d.pct}%`,
                backgroundColor: STAR_COLORS[d.stars] || '#9ca3af'
              }}
            />
          </div>
          <div className="w-8 text-[11px] font-bold text-gray-400 text-right">{d.pct}%</div>
        </div>
      ))}
    </div>
  )
}
