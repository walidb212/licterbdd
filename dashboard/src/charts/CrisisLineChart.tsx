import { AreaChart } from '@tremor/react'

interface Props {
  data: { date: string; volume: number }[]
}

export default function CrisisLineChart({ data }: Props) {
  const display = data.slice(-30).map(d => ({ ...d, date: d.date.slice(5) }))

  return (
    <AreaChart
      data={display}
      index="date"
      categories={['volume']}
      colors={['rose']}
      showLegend={false}
      showGradient={true}
      showAnimation={true}
      curveType="monotone"
      className="h-44"
      yAxisWidth={40}
    />
  )
}
