import { AreaChart } from '@tremor/react'

interface Props {
  data: { month: string; decathlon: number | null; intersport: number | null }[]
}

export default function RatingLineChart({ data }: Props) {
  return (
    <AreaChart
      data={data}
      index="month"
      categories={['decathlon', 'intersport']}
      colors={['blue', 'red']}
      showAnimation={true}
      connectNulls={true}
      className="h-56"
      yAxisWidth={35}
      valueFormatter={(v) => `${v.toFixed(1)} ★`}
      curveType="monotone"
      minValue={0}
      maxValue={5}
      showGradient={true}
    />
  )
}
