import { motion } from 'motion/react'
import { Clock, Eye } from 'lucide-react'
import { Badge, BiasSpectrum } from '@/components/ui'
import { categories } from '@/lib/data'
import type { Article } from '@/types'

interface HeroArticleProps {
  article: Article
}

export function HeroArticle({ article }: HeroArticleProps) {
  return (
    <motion.a
      href={`/article/${article.slug}`}
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.1 }}
      className="lg:col-span-7 lg:row-span-2 group"
    >
      <div className="relative h-full min-h-[400px] lg:min-h-[520px] rounded-[var(--radius-xl)] overflow-hidden">
        <img
          src={article.imageUrl}
          alt={article.imageAlt}
          className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

        {/* Content */}
        <div className="absolute inset-0 p-6 md:p-8 flex flex-col justify-end">
          <div className="flex items-center gap-3 mb-4">
            {article.isBreaking && (
              <Badge variant="accent" pulse>Breaking</Badge>
            )}
            <Badge variant="outline" className="bg-white/10 border-white/20 text-white">
              {categories.find(c => c.id === article.category)?.label}
            </Badge>
          </div>

          <h2 className="heading-display text-2xl md:text-3xl lg:text-4xl text-white mb-4 group-hover:text-[var(--color-accent-trust)] transition-colors">
            {article.headline}
          </h2>

          <p className="text-white/80 mb-4 line-clamp-2 max-w-2xl">
            {article.summary}
          </p>

          <div className="flex items-center gap-4 text-sm text-white/60">
            <span className="flex items-center gap-1.5">
              <Eye className="w-4 h-4" />
              {article.sources.length} sources
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              {article.readTime} min
            </span>
            <div className="flex-1 max-w-[150px]">
              <BiasSpectrum distribution={article.biasDistribution} size="sm" showLabels={false} />
            </div>
          </div>
        </div>
      </div>
    </motion.a>
  )
}
