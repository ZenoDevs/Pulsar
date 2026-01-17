import { motion } from 'motion/react'
import { TrendingUp } from 'lucide-react'

const topics = [
  'Climate Summit',
  'AI Regulation',
  'Federal Reserve',
  'Mars Discovery',
  'Quantum Computing',
  'Trade Agreement',
]

export function TrendingTopics() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
      className="mt-12"
    >
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-[var(--color-accent-pulse)]" />
        <h3 className="heading-sans text-lg text-[var(--color-text-primary)]">Trending Now</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {topics.map((topic) => (
          <a
            key={topic}
            href={`/topic/${topic.toLowerCase().replace(' ', '-')}`}
            className="px-4 py-2 text-sm text-[var(--color-text-secondary)] bg-[var(--color-surface-glass)] backdrop-blur-sm border border-[var(--color-border-glass)] rounded-full hover:bg-[var(--color-surface-tertiary)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            {topic}
          </a>
        ))}
      </div>
    </motion.section>
  )
}
