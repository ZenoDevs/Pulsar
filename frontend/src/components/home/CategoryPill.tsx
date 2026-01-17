interface CategoryPillProps {
  label: string
  isActive: boolean
  onClick: () => void
  count: number
}

export function CategoryPill({ label, isActive, onClick, count }: CategoryPillProps) {
  return (
    <button
      onClick={onClick}
      className={`
        relative px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap
        transition-all duration-200
        ${isActive
          ? 'bg-[var(--color-text-primary)] text-[var(--color-surface-primary)]'
          : 'bg-[var(--color-surface-glass)] backdrop-blur-sm border border-[var(--color-border-glass)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] hover:text-[var(--color-text-primary)]'
        }
      `}
    >
      {label}
      <span
        className={`ml-1.5 text-xs ${isActive ? 'opacity-70' : 'text-[var(--color-text-muted)]'}`}
      >
        {count}
      </span>
    </button>
  )
}
