import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface Props {
  data: { month: string; decathlon: number | null; intersport: number | null }[]
}

export default function RatingLineChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis dataKey="month" tick={{ fill: '#6b7d91', fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis domain={[1, 5]} tick={{ fill: '#6b7d91', fontSize: 10 }} ticks={[1, 2, 3, 4, 5]} />
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          formatter={(v: unknown) => [`${v} ★`]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span style={{ color: '#a8b8cc', fontSize: 11 }}>{v === 'decathlon' ? 'Decathlon' : 'Intersport'}</span>}
        />
        <Line
          type="monotone"
          dataKey="decathlon"
          stroke="#0077c8"
          strokeWidth={2}
          dot={false}
          connectNulls
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="intersport"
          stroke="#e8001c"
          strokeWidth={2}
          dot={false}
          connectNulls
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
