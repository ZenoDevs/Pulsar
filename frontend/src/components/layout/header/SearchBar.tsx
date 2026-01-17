import { motion } from 'motion/react'
import { Search, X } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  isExpanded: boolean
  onExpandChange: (expanded: boolean) => void
}

export function SearchBar({
  value,
  onChange,
  isExpanded,
  onExpandChange,
}: SearchBarProps) {
  return (
    <motion.div
      initial={false}
      animate={{ width: isExpanded ? 260 : 140 }}
      transition={{ duration: 0.15, ease: 'easeInOut' }}
      className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-tertiary focus-within:ring-2 focus-within:ring-accent-pulse/30 focus-within:bg-surface-secondary transition-all"
    >
      <Search className="w-4 h-4 text-text-muted shrink-0" />
      <input
        type="text"
        id="header-search"
        placeholder={isExpanded ? "Search stories, topics..." : "Search..."}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => onExpandChange(true)}
        onBlur={() => {
          if (!value) onExpandChange(false)
        }}
        style={{ outline: 'none', boxShadow: 'none' }}
        className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted border-none min-w-0 focus:outline-none focus:ring-0 focus:border-none focus:shadow-none"
      />
      {isExpanded && value && (
        <button
          onClick={() => {
            onChange('')
            onExpandChange(false)
          }}
          className="p-0.5 rounded text-text-muted hover:text-text-primary"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </motion.div>
  )
}
