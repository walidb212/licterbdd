import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface Props {
  data: { month: string; decathlon: number; intersport: number }[]
}

export default function SovBarChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis
          dataKey="month"
          tick={{ fill: '#6b7d91', fontSize: 10 }}
          interval={Math.max(0, Math.floor(data.length / 6) - 1)}
        />
        <YAxis tick={{ fill: '#6b7d91', fontSize: 10 }} domain={[0, 100]} unit="%" />
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          formatter={(v: unknown) => [`${v}%`]}
        />
        <Legend
          iconType="square"
          iconSize={8}
          formatter={(v) => <span style={{ color: '#a8b8cc', fontSize: 11 }}>{v === 'decathlon' ? 'Decathlon' : 'Intersport'}</span>}
        />
        <Bar dataKey="decathlon" stackId="a" fill="#0077c8" radius={[0, 0, 0, 0]} />
        <Bar dataKey="intersport" stackId="a" fill="#e8001c" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
