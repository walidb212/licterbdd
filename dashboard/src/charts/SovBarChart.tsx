import { BarChart } from '@tremor/react'

interface Props {
  data: { month: string; decathlon: number; intersport: number }[]
}

export default function SovBarChart({ data }: Props) {
  return (
    <BarChart
      data={data}
      index="month"
      categories={['decathlon', 'intersport']}
      colors={['blue', 'rose']}
      stack={true}
      showAnimation={true}
      showLegend={true}
      className="h-56"
      yAxisWidth={45}
      valueFormatter={(v) => `${v}%`}
    />
  )
}
