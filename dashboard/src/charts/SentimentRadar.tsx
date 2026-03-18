import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend, ResponsiveContainer, Tooltip,
} from 'recharts'

interface Props {
  data: { topic: string; decathlon: number; intersport: number }[]
}

export default function SentimentRadar({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data}>
        <PolarGrid stroke="#2d3748" />
        <PolarAngleAxis dataKey="topic" tick={{ fill: '#a8b8cc', fontSize: 11 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7d91', fontSize: 9 }} />
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          formatter={(v: unknown) => [`${v}%`]}
        />
        <Radar name="Decathlon" dataKey="decathlon" stroke="#0077c8" fill="#0077c8" fillOpacity={0.2} />
        <Radar name="Intersport" dataKey="intersport" stroke="#e8001c" fill="#e8001c" fillOpacity={0.2} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span style={{ color: '#a8b8cc', fontSize: 11 }}>{v}</span>}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
