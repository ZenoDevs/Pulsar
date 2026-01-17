import { motion } from 'motion/react'
import { Search, Sparkles } from 'lucide-react'
import { GlassCard } from '@/components/ui'
import { mockArticles } from '@/lib/data'

interface SearchSectionProps {
  searchQuery: string
  onSearchChange: (value: string) => void
}

export function SearchSection({ searchQuery, onSearchChange }: SearchSectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-12"
    >
      {/* Brand + Tagline */}
      <div className="text-center mb-8">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-[var(--color-text-secondary)] text-lg"
        >
          Every perspective. Full transparency.
        </motion.p>
      </div>

      {/* Search Bar */}
      <div className="max-w-2xl mx-auto">
        <GlassCard padding="none" hover={false} className="rounded-full!">
          <div className="flex items-center px-6 py-4">
            <Search className="w-5 h-5 text-[var(--color-text-muted)] shrink-0" />
            <input
              type="text"
              placeholder="Search stories, topics, sources..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="flex-1 px-4 py-1 bg-transparent text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none text-lg"
            />
            <div className="hidden sm:flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
              <Sparkles className="w-4 h-4" />
              <span>AI-powered</span>
            </div>
          </div>
        </GlassCard>

        {/* Quick stats */}
        <div className="flex items-center justify-center gap-6 mt-4 text-sm text-[var(--color-text-muted)]">
          <span>{mockArticles.length} stories</span>
          <span className="w-1 h-1 rounded-full bg-[var(--color-text-muted)]" />
          <span>500+ sources</span>
          <span className="w-1 h-1 rounded-full bg-[var(--color-text-muted)]" />
          <span>Updated live</span>
        </div>
      </div>
    </motion.section>
  )
}
