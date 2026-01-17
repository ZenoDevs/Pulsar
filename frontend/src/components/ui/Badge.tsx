import { motion } from 'motion/react'
import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning' | 'outline'
  size?: 'sm' | 'md'
  pulse?: boolean
  className?: string
}

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  pulse = false,
  className = '',
}: BadgeProps) {
  const baseClasses = `
    inline-flex items-center justify-center
    font-medium rounded-full
    whitespace-nowrap
  `

  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-sm px-3 py-1',
  }

  const variantClasses = {
    default: `
      bg-[var(--color-surface-tertiary)]
      text-[var(--color-text-secondary)]
    `,
    accent: `
      bg-[var(--color-accent-pulse-soft)]
      text-[var(--color-accent-pulse)]
    `,
    success: `
      bg-[var(--color-accent-trust-soft)]
      text-[var(--color-accent-trust)]
    `,
    warning: `
      bg-[var(--color-accent-warm-soft)]
      text-[var(--color-accent-warm)]
    `,
    outline: `
      bg-transparent
      border border-[var(--color-border-primary)]
      text-[var(--color-text-secondary)]
    `,
  }

  return (
    <motion.span
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      {pulse && (
        <span className="relative flex h-2 w-2 mr-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
        </span>
      )}
      {children}
    </motion.span>
  )
}
