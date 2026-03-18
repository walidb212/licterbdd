import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Props {
  data: { platform: string; count: number; pct: number }[]
}

const COLORS = ['#0077c8', '#4ecdc4', '#ffd93d', '#ff6b6b', '#6c9fe6', '#a8b8cc']

export default function PlatformPieChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="platform"
          cx="50%"
          cy="50%"
          outerRadius={80}
          labelLine={false}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(v: any, name: any) => [`${v} mentions`, name]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span style={{ color: '#a8b8cc', fontSize: 11 }}>{v}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
