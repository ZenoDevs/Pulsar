import { motion } from 'motion/react'
import { Clock, ArrowUpRight } from 'lucide-react'
import { BiasSpectrum } from '@/components/ui'
import { categories } from '@/lib/data'
import type { Article } from '@/types'

interface ArticleRowProps {
  article: Article
  index: number
}

function getTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function ArticleRow({ article, index }: ArticleRowProps) {
  const category = categories.find((c) => c.id === article.category)
  const timeAgo = getTimeAgo(article.publishedAt)

  return (
    <motion.a
      href={`/article/${article.slug}`}
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: index * 0.03 }}
      className="group block"
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 px-6 py-4 h-[88px] hover:bg-[var(--color-surface-tertiary)]/50 transition-colors">
        {/* Story */}
        <div className="md:col-span-6 flex gap-4 items-center">
          <img
            src={article.imageUrl}
            alt=""
            className="w-14 h-14 rounded-[var(--radius-md)] object-cover shrink-0"
          />
          <div className="flex-1 min-w-0">
            <h3 className="heading-sans text-[var(--color-text-primary)] group-hover:text-[var(--color-accent-pulse)] transition-colors line-clamp-1 text-base">
              {article.headline}
            </h3>
            <p className="text-sm text-[var(--color-text-muted)] mt-1 line-clamp-1 hidden md:block">
              {article.summary}
            </p>
          </div>
        </div>

        {/* Category */}
        <div className="md:col-span-2 flex items-center">
          {category && (
            <span
              className="text-sm font-medium"
              style={{ color: category.color }}
            >
              {category.label}
            </span>
          )}
        </div>

        {/* Sources */}
        <div className="md:col-span-2 flex items-center gap-3">
          <div className="flex-1 max-w-[120px]">
            <BiasSpectrum
              distribution={article.biasDistribution}
              size="sm"
              showLabels={false}
            />
          </div>
          <span className="text-sm text-[var(--color-text-muted)] whitespace-nowrap">
            {article.sources.length}
          </span>
        </div>

        {/* Time */}
        <div className="md:col-span-2 flex items-center justify-end gap-2">
          <span className="text-sm text-[var(--color-text-muted)] flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            {timeAgo}
          </span>
          <ArrowUpRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>
    </motion.a>
  )
}
