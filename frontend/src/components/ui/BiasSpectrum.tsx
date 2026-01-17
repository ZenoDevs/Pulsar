import { motion } from 'motion/react'

interface BiasSpectrumProps {
  distribution: {
    left: number
    leanLeft: number
    center: number
    leanRight: number
    right: number
  }
  showLabels?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function BiasSpectrum({
  distribution,
  showLabels = true,
  size = 'md',
  className = '',
}: BiasSpectrumProps) {
  const total =
    distribution.left +
    distribution.leanLeft +
    distribution.center +
    distribution.leanRight +
    distribution.right

  const segments = [
    { key: 'left', label: 'Left', value: distribution.left, color: 'var(--color-bias-left)' },
    {
      key: 'leanLeft',
      label: 'Lean Left',
      value: distribution.leanLeft,
      color: 'color-mix(in oklch, var(--color-bias-left) 60%, var(--color-bias-center))',
    },
    { key: 'center', label: 'Center', value: distribution.center, color: 'var(--color-bias-center)' },
    {
      key: 'leanRight',
      label: 'Lean Right',
      value: distribution.leanRight,
      color: 'color-mix(in oklch, var(--color-bias-right) 60%, var(--color-bias-center))',
    },
    { key: 'right', label: 'Right', value: distribution.right, color: 'var(--color-bias-right)' },
  ]

  const heights = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }

  return (
    <div className={`w-full ${className}`}>
      <div
        className={`flex ${heights[size]} rounded-full overflow-hidden bg-[var(--color-surface-tertiary)]`}
      >
        {segments.map((segment, index) => {
          const percentage = total > 0 ? (segment.value / total) * 100 : 0
          if (percentage === 0) return null

          return (
            <motion.div
              key={segment.key}
              className="h-full"
              style={{ backgroundColor: segment.color }}
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{
                type: 'spring',
                stiffness: 100,
                damping: 20,
                delay: index * 0.05,
              }}
            />
          )
        })}
      </div>

      {showLabels && (
        <div className="flex justify-between mt-2 text-xs text-[var(--color-text-muted)]">
          <span>Left</span>
          <span>Center</span>
          <span>Right</span>
        </div>
      )}
    </div>
  )
}

interface BiasIndicatorProps {
  bias: string
  size?: 'sm' | 'md'
  showLabel?: boolean
}

export function BiasIndicator({ bias, size = 'sm', showLabel = true }: BiasIndicatorProps) {
  const positions: Record<string, number> = {
    left: 0,
    'lean-left': 25,
    center: 50,
    'lean-right': 75,
    right: 100,
  }

  const labels: Record<string, string> = {
    left: 'Left',
    'lean-left': 'Lean Left',
    center: 'Center',
    'lean-right': 'Lean Right',
    right: 'Right',
  }

  const position = positions[bias] ?? 50
  const dotSize = size === 'sm' ? 'w-2 h-2' : 'w-3 h-3'

  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative h-1.5 rounded-full bg-gradient-to-r from-[var(--color-bias-left)] via-[var(--color-bias-center)] to-[var(--color-bias-right)]">
        <motion.div
          className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 ${dotSize} rounded-full bg-white border-2 border-[var(--color-text-primary)] shadow-md`}
          initial={{ left: '50%' }}
          animate={{ left: `${position}%` }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-[var(--color-text-tertiary)]">{labels[bias]}</span>
      )}
    </div>
  )
}
