import { motion } from 'motion/react'
import { Clock, Eye } from 'lucide-react'
import { GlassCard, Badge, BiasSpectrum } from '@/components/ui'
import type { Article } from '@/types'
import { categories } from '@/lib/data'

interface ArticleCardProps {
  article: Article
  variant?: 'default' | 'featured' | 'compact'
  index?: number
}

export function ArticleCard({ article, variant = 'default', index = 0 }: ArticleCardProps) {
  const category = categories.find((c) => c.id === article.category)
  const formattedDate = new Date(article.publishedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })

  if (variant === 'featured') {
    return (
      <motion.a
        href={`/article/${article.slug}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1, type: 'spring', stiffness: 100 }}
        className="group block"
      >
        <GlassCard padding="none" className="overflow-hidden">
          <div className="grid md:grid-cols-2 gap-0">
            {/* Image */}
            <div className="relative aspect-[16/10] md:aspect-auto overflow-hidden">
              <motion.img
                src={article.imageUrl}
                alt={article.imageAlt}
                className="absolute inset-0 w-full h-full object-cover"
                whileHover={{ scale: 1.05 }}
                transition={{ duration: 0.6 }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent md:bg-gradient-to-r" />

              {/* Badges */}
              <div className="absolute top-4 left-4 flex items-center gap-2">
                {article.isBreaking && (
                  <Badge variant="accent" pulse>
                    Breaking
                  </Badge>
                )}
                {category && (
                  <Badge variant="outline" className="bg-white/20 backdrop-blur-sm border-white/30 text-white">
                    {category.label}
                  </Badge>
                )}
              </div>
            </div>

            {/* Content */}
            <div className="p-6 md:p-8 flex flex-col justify-center">
              <h2 className="heading-display text-2xl md:text-3xl text-[var(--color-text-primary)] mb-4 group-hover:gradient-text transition-all duration-300">
                {article.headline}
              </h2>

              <p className="text-[var(--color-text-secondary)] mb-6 line-clamp-3">
                {article.summary}
              </p>

              {/* Bias spectrum */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Eye className="w-4 h-4 text-[var(--color-text-muted)]" />
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {article.sources.length} sources across the spectrum
                  </span>
                </div>
                <BiasSpectrum distribution={article.biasDistribution} size="sm" showLabels={false} />
              </div>

              {/* Meta */}
              <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                <span>{formattedDate}</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {article.readTime} min read
                </span>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.a>
    )
  }

  if (variant === 'compact') {
    return (
      <motion.a
        href={`/article/${article.slug}`}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.05, type: 'spring', stiffness: 100 }}
        className="group flex gap-4 py-4 border-b border-[var(--color-border-glass)] last:border-b-0"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            {category && (
              <span className="text-xs font-medium" style={{ color: category.color }}>
                {category.label}
              </span>
            )}
            <span className="text-xs text-[var(--color-text-muted)]">{formattedDate}</span>
          </div>
          <h3 className="text-[var(--color-text-primary)] font-medium line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
            {article.headline}
          </h3>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-[var(--color-text-muted)]">
              {article.sources.length} sources
            </span>
          </div>
        </div>
        <div className="w-20 h-20 rounded-[var(--radius-md)] overflow-hidden shrink-0">
          <img
            src={article.imageUrl}
            alt=""
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
      </motion.a>
    )
  }

  // Default card
  return (
    <motion.a
      href={`/article/${article.slug}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, type: 'spring', stiffness: 100 }}
      className="group block"
    >
      <GlassCard padding="none" className="overflow-hidden h-full flex flex-col">
        {/* Image */}
        <div className="relative aspect-[16/10] overflow-hidden">
          <motion.img
            src={article.imageUrl}
            alt={article.imageAlt}
            className="absolute inset-0 w-full h-full object-cover"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.6 }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />

          {/* Category badge */}
          {category && (
            <div className="absolute top-3 left-3">
              <Badge variant="outline" className="bg-white/20 backdrop-blur-sm border-white/30 text-white text-xs">
                {category.label}
              </Badge>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-5 flex-1 flex flex-col">
          <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-3 line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
            {article.headline}
          </h3>

          <p className="text-sm text-[var(--color-text-secondary)] mb-4 line-clamp-2 flex-1">
            {article.summary}
          </p>

          {/* Sources indicator */}
          <div className="mb-3">
            <BiasSpectrum distribution={article.biasDistribution} size="sm" showLabels={false} />
          </div>

          {/* Meta */}
          <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
            <span>{formattedDate}</span>
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {article.sources.length} sources
            </span>
          </div>
        </div>
      </GlassCard>
    </motion.a>
  )
}
