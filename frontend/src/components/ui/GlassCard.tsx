import { forwardRef, type ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  variant?: 'default' | 'subtle' | 'elevated'
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  className?: string
}

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ children, variant = 'default', hover = true, padding = 'md', className = '' }, ref) => {
    const baseClasses = `
      relative overflow-hidden rounded-[var(--radius-lg)]
      bg-[var(--color-surface-glass)]
      backdrop-blur-[var(--blur-glass)]
      border border-[var(--color-border-glass)]
      transition-all duration-300 ease-out
      ${paddingClasses[padding]}
    `

    const variantClasses = {
      default: 'shadow-[var(--shadow-glass)]',
      subtle: 'shadow-[var(--shadow-subtle)]',
      elevated: 'shadow-[var(--shadow-elevated)]',
    }

    const hoverClasses = hover
      ? 'hover:-translate-y-1 hover:shadow-[var(--shadow-glass-hover)]'
      : ''

    return (
      <div
        ref={ref}
        className={`${baseClasses} ${variantClasses[variant]} ${hoverClasses} ${className}`}
      >
        {children}
      </div>
    )
  }
)

GlassCard.displayName = 'GlassCard'
