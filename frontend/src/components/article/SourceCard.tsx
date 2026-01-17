import { motion } from 'motion/react'
import { ExternalLink, Shield } from 'lucide-react'
import { GlassCard, BiasIndicator } from '@/components/ui'
import type { ArticleSource } from '@/types'
import { getBiasLabel } from '@/lib/data'

interface SourceCardProps {
  articleSource: ArticleSource
  index?: number
}

export function SourceCard({ articleSource, index = 0 }: SourceCardProps) {
  const { source, url, title, publishedAt, excerpt } = articleSource

  const formattedDate = new Date(publishedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, type: 'spring', stiffness: 100 }}
    >
      <GlassCard padding="md" className="h-full">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-[var(--color-text-primary)] truncate">
                {source.name}
              </h4>
              <span className="text-xs text-[var(--color-text-muted)] shrink-0">
                {source.country}
              </span>
            </div>
            <BiasIndicator bias={source.bias} size="sm" />
          </div>

          {/* Reliability score */}
          <div className="flex items-center gap-1.5 shrink-0">
            <Shield className="w-4 h-4 text-[var(--color-accent-trust)]" />
            <span className="text-sm font-medium text-[var(--color-text-secondary)]">
              {source.reliability}%
            </span>
          </div>
        </div>

        {/* Article info */}
        <div className="space-y-3">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="block group"
          >
            <h5 className="text-[var(--color-text-primary)] font-medium line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
              {title}
            </h5>
          </a>

          <p className="text-sm text-[var(--color-text-secondary)] line-clamp-2">
            {excerpt}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-glass)]">
          <span className="text-xs text-[var(--color-text-muted)]">{formattedDate}</span>
          <motion.a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs font-medium text-[var(--color-accent-pulse)] hover:underline"
            whileHover={{ x: 2 }}
          >
            Read original
            <ExternalLink className="w-3 h-3" />
          </motion.a>
        </div>
      </GlassCard>
    </motion.div>
  )
}

interface SourceListProps {
  sources: ArticleSource[]
}

export function SourceList({ sources }: SourceListProps) {
  // Group sources by bias
  const groupedSources = sources.reduce(
    (acc, source) => {
      const bias = source.source.bias
      if (!acc[bias]) acc[bias] = []
      acc[bias].push(source)
      return acc
    },
    {} as Record<string, ArticleSource[]>
  )

  const biasOrder = ['left', 'lean-left', 'center', 'lean-right', 'right']

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h3 className="heading-sans text-xl text-[var(--color-text-primary)]">
          Sources ({sources.length})
        </h3>
        <div className="text-sm text-[var(--color-text-muted)]">
          Across {Object.keys(groupedSources).length} perspectives
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {biasOrder.map((bias) =>
          groupedSources[bias]?.map((source, i) => (
            <SourceCard
              key={`${source.source.id}-${i}`}
              articleSource={source}
              index={i}
            />
          ))
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-4 pt-6 border-t border-[var(--color-border-glass)]">
        {biasOrder.map((bias) => (
          <div key={bias} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor:
                  bias === 'left'
                    ? 'var(--color-bias-left)'
                    : bias === 'right'
                      ? 'var(--color-bias-right)'
                      : 'var(--color-bias-center)',
                opacity: bias.includes('lean') ? 0.7 : 1,
              }}
            />
            <span className="text-xs text-[var(--color-text-muted)]">
              {getBiasLabel(bias)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
