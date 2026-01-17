import { motion } from 'motion/react'
import { Clock, Eye, ArrowUpRight } from 'lucide-react'
import { GlassCard } from '@/components/ui'
import { categories } from '@/lib/data'
import type { Article } from '@/types'

interface FeaturedCardProps {
  article: Article
  index: number
  variant?: 'default' | 'horizontal'
}

export function FeaturedCard({ article, index, variant = 'default' }: FeaturedCardProps) {
  const category = categories.find((c) => c.id === article.category)

  if (variant === 'horizontal') {
    return (
      <motion.a
        href={`/article/${article.slug}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 + index * 0.1 }}
        className="group"
      >
        <GlassCard padding="none" hover={true} className="overflow-hidden">
          <div className="flex flex-col sm:flex-row">
            <div className="relative w-full sm:w-48 h-40 sm:h-auto shrink-0">
              <img
                src={article.imageUrl}
                alt={article.imageAlt}
                className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            </div>
            <div className="p-5 flex-1">
              {category && (
                <span className="text-xs font-medium mb-2 block" style={{ color: category.color }}>
                  {category.label}
                </span>
              )}
              <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-2 line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
                {article.headline}
              </h3>
              <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
                <span className="flex items-center gap-1">
                  <Eye className="w-3.5 h-3.5" />
                  {article.sources.length}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {article.readTime}m
                </span>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.a>
    )
  }

  return (
    <motion.a
      href={`/article/${article.slug}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 + index * 0.1 }}
      className="group flex-1"
    >
      <GlassCard padding="none" hover={true} className="h-full overflow-hidden">
        <div className="relative h-32 md:h-40">
          <img
            src={article.imageUrl}
            alt={article.imageAlt}
            className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        </div>
        <div className="p-5">
          {category && (
            <span className="text-xs font-medium mb-2 block" style={{ color: category.color }}>
              {category.label}
            </span>
          )}
          <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-2 line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
            {article.headline}
          </h3>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                {article.sources.length}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {article.readTime}m
              </span>
            </div>
            <ArrowUpRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </GlassCard>
    </motion.a>
  )
}
