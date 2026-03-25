import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Props {
  data: { platform: string; count: number; pct: number }[]
}

const COLORS = ['#3b82f6', '#06b6d4', '#f59e0b', '#ef4444', '#6366f1', '#94a3b8']

export default function PlatformPieChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="platform"
          cx="50%"
          cy="45%"
          innerRadius={45}
          outerRadius={70}
          strokeWidth={2}
          stroke="#fff"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
          formatter={(v: unknown, name: unknown) => [`${v} mentions`, name]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v, entry) => {
            const item = data.find(d => d.platform === v)
            return <span style={{ color: '#374151', fontSize: 12 }}>{v} {item ? `${item.pct}%` : ''}</span>
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
