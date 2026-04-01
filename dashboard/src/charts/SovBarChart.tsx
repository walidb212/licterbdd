import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Props {
  data: { month: string; decathlon: number; intersport: number }[]
}

export default function SovBarChart({ data }: Props) {
  return (
    <div className="h-56 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data.slice(-3)} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorDecathlon" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#324DE6" stopOpacity={0.9}/>
              <stop offset="95%" stopColor="#324DE6" stopOpacity={0.6}/>
            </linearGradient>
            <linearGradient id="colorIntersport" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#e8001c" stopOpacity={0.9}/>
              <stop offset="95%" stopColor="#e8001c" stopOpacity={0.6}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11 }} tickLine={false} axisLine={false} dy={5} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} width={60} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)', padding: '8px 12px' }}
            itemStyle={{ padding: 0 }}
            formatter={(v: unknown) => [`${v}%`]}
            labelStyle={{ color: '#6b7280', fontWeight: 'bold', marginBottom: 4 }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: 11, color: '#6b7280', paddingTop: 10 }}
          />
          <Area type="monotone" dataKey="intersport" name="Intersport" stackId="1" stroke="#e8001c" strokeWidth={2} fill="url(#colorIntersport)" />
          <Area type="monotone" dataKey="decathlon" name="Decathlon" stackId="1" stroke="#324DE6" strokeWidth={2} fill="url(#colorDecathlon)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
