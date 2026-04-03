import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend, ResponsiveContainer, Tooltip,
} from 'recharts'

interface Props {
  data: { topic: string; decathlon: number; intersport: number }[]
}

export default function SentimentRadar({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="topic" tick={{ fill: '#6b7280', fontSize: 11 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 9 }} />
        <Tooltip
          contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
          formatter={(v: unknown) => [`${v}%`]}
        />
        <Radar name="Decathlon" dataKey="decathlon" stroke="#324DE6" fill="#324DE6" fillOpacity={0.15} strokeWidth={2} />
        <Radar name="Intersport" dataKey="intersport" stroke="#e8001c" fill="#e8001c" fillOpacity={0.15} strokeWidth={2} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span style={{ color: '#6b7280', fontSize: 11 }}>{v}</span>}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
