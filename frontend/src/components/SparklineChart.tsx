import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface Props {
  data: { price: number }[]
}

export default function SparklineChart({ data }: Props) {
  if (!data || data.length < 2) return null

  return (
    <div className="w-full h-8">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
