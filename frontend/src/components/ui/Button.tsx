import { motion, type HTMLMotionProps } from 'motion/react'
import { forwardRef, type ReactNode } from 'react'

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'glass'
  size?: 'sm' | 'md' | 'lg'
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      icon,
      iconPosition = 'left',
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseClasses = `
      inline-flex items-center justify-center gap-2
      font-medium transition-colors
      focus:outline-none focus-visible:ring-2
      focus-visible:ring-[var(--color-accent-pulse)]
      focus-visible:ring-offset-2
      disabled:opacity-50 disabled:pointer-events-none
      rounded-[var(--radius-md)]
    `

    const sizeClasses = {
      sm: 'text-sm px-3 py-1.5',
      md: 'text-sm px-4 py-2.5',
      lg: 'text-base px-6 py-3',
    }

    const variantClasses = {
      primary: `
        bg-[var(--color-text-primary)]
        text-[var(--color-surface-primary)]
        hover:opacity-90
      `,
      secondary: `
        bg-[var(--color-surface-tertiary)]
        text-[var(--color-text-primary)]
        hover:bg-[var(--color-border-primary)]
      `,
      ghost: `
        bg-transparent
        text-[var(--color-text-secondary)]
        hover:bg-[var(--color-surface-tertiary)]
        hover:text-[var(--color-text-primary)]
      `,
      glass: `
        bg-[var(--color-surface-glass)]
        backdrop-blur-[var(--blur-glass)]
        border border-[var(--color-border-glass)]
        text-[var(--color-text-primary)]
        shadow-[var(--shadow-subtle)]
        hover:bg-[var(--color-surface-glass-hover)]
        hover:shadow-[var(--shadow-glass)]
      `,
    }

    return (
      <motion.button
        ref={ref}
        className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
        whileHover={{ scale: disabled ? 1 : 1.02 }}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        disabled={disabled}
        {...props}
      >
        {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
        {children}
        {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'
