import clsx from 'clsx'

export default function DealScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-red-500 border-red-500' :
    score >= 60 ? 'text-green-500 border-green-500' :
    score >= 40 ? 'text-amber-500 border-amber-500' :
    'text-gray-400 border-gray-400'

  return (
    <div className={clsx('flex items-center justify-center w-10 h-10 rounded-full border-2 text-xs font-bold', color)}>
      {score}
    </div>
  )
}
