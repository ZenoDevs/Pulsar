import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/context/ThemeContext'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { resolvedTheme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative p-2.5 rounded-[var(--radius-md)]
        bg-[var(--color-surface-glass)]
        backdrop-blur-[var(--blur-glass)]
        border border-[var(--color-border-glass)]
        text-[var(--color-text-secondary)]
        hover:text-[var(--color-text-primary)]
        hover:bg-[var(--color-surface-glass-hover)]
        transition-all duration-200
        ${className}
      `}
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {resolvedTheme === 'dark' ? (
        <Sun className="w-5 h-5" />
      ) : (
        <Moon className="w-5 h-5" />
      )}
    </button>
  )
}
