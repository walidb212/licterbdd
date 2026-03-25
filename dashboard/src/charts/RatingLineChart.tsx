import { LineChart } from '@tremor/react'

interface Props {
  data: { month: string; decathlon: number | null; intersport: number | null }[]
}

export default function RatingLineChart({ data }: Props) {
  return (
    <LineChart
      data={data}
      index="month"
      categories={['decathlon', 'intersport']}
      colors={['blue', 'rose']}
      showAnimation={true}
      connectNulls={true}
      className="h-56"
      yAxisWidth={30}
      valueFormatter={(v) => `${v} ★`}
      curveType="monotone"
    />
  )
}
