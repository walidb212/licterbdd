import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer,
} from 'recharts'

interface Props {
  data: { stars: number; count: number; pct: number }[]
}

const STAR_COLORS: Record<number, string> = {
  1: '#ff6b6b',
  2: '#ffa94d',
  3: '#ffd93d',
  4: '#74c0fc',
  5: '#4ecdc4',
}

export default function RatingDistBar({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 32, left: 4, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" horizontal={false} />
        <XAxis type="number" tick={{ fill: '#6b7d91', fontSize: 10 }} unit="%" domain={[0, 100]} />
        <YAxis
          type="category"
          dataKey="stars"
          tick={{ fill: '#a8b8cc', fontSize: 11 }}
          tickFormatter={(v: number) => `${v}★`}
          width={28}
        />
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(v: any, _: any, entry: any) => [`${v}% (${entry?.payload?.count ?? ''})`, `${entry?.payload?.stars ?? ''}★`]}
        />
        <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
          {data.map((entry) => (
            <Cell key={entry.stars} fill={STAR_COLORS[entry.stars] ?? '#a8b8cc'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
