import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

interface Props {
  data: { date: string; volume: number }[]
}

export default function CrisisLineChart({ data }: Props) {
  const display = data.slice(-30)
  // Find the peak date dynamically
  const peakDate = display.length > 0
    ? display.reduce((max, d) => d.volume > max.volume ? d : max, display[0]).date
    : null

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={display} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#6b7d91', fontSize: 10 }}
          tickFormatter={(v: string) => v.slice(5)}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: '#6b7d91', fontSize: 10 }} />
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #2d3748', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#a8b8cc' }}
          itemStyle={{ color: '#ff6b6b' }}
        />
        {peakDate && (
          <ReferenceLine
            x={peakDate}
            stroke="#ff6b6b"
            strokeDasharray="4 3"
            label={{ value: 'Pic crise', position: 'top', fill: '#ff6b6b', fontSize: 10 }}
          />
        )}
        <Line
          type="monotone"
          dataKey="volume"
          stroke="#ff6b6b"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: '#ff6b6b' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
