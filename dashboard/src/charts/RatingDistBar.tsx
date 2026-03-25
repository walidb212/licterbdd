import { BarList } from '@tremor/react'

interface Props {
  data: { stars: number; count: number; pct: number }[]
}

const STAR_COLORS: Record<number, string> = {
  1: 'rose', 2: 'orange', 3: 'amber', 4: 'blue', 5: 'emerald',
}

export default function RatingDistBar({ data }: Props) {
  const barData = data.map(d => ({
    name: `${d.stars}★`,
    value: d.pct,
    color: STAR_COLORS[d.stars] || 'gray',
  })).reverse()

  return (
    <BarList
      data={barData}
      showAnimation={true}
      className="mt-2"
      valueFormatter={(v) => `${v}%`}
    />
  )
}
