import { motion } from 'motion/react'
import { Clock, Share2, Bookmark, ArrowLeft, TrendingUp } from 'lucide-react'
import { GlassCard, Badge, Button, BiasSpectrum } from '@/components/ui'
import { SourceList, ArticleCard } from '@/components/article'
import { getArticleBySlug, mockArticles, categories } from '@/lib/data'

interface ArticlePageProps {
  slug?: string
}

export function ArticlePage({ slug = 'global-climate-summit-reaches-historic-agreement' }: ArticlePageProps) {
  const article = getArticleBySlug(slug)

  if (!article) {
    return (
      <div className="container-narrow py-20 text-center">
        <h1 className="heading-display text-4xl mb-4">Article not found</h1>
        <p className="text-[var(--color-text-secondary)] mb-8">
          The article you're looking for doesn't exist or has been removed.
        </p>
        <Button variant="primary" onClick={() => window.history.back()}>
          Go back
        </Button>
      </div>
    )
  }

  const category = categories.find((c) => c.id === article.category)
  const formattedDate = new Date(article.publishedAt).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const relatedArticles = mockArticles
    .filter((a) => a.id !== article.id && a.category === article.category)
    .slice(0, 3)

  return (
    <article>
      {/* Hero section */}
      <section className="relative">
        {/* Background image with overlay */}
        <div className="absolute inset-0 h-[60vh] min-h-[500px]">
          <img
            src={article.imageUrl}
            alt={article.imageAlt}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-[var(--color-surface-primary)]" />
        </div>

        {/* Content */}
        <div className="relative container-wide pt-12 pb-32">
          {/* Back button */}
          <motion.a
            href="/"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="inline-flex items-center gap-2 text-white/80 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to stories
          </motion.a>

          {/* Article header */}
          <div className="max-w-4xl">
            {/* Badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="flex flex-wrap items-center gap-3 mb-6"
            >
              {article.isBreaking && (
                <Badge variant="accent" pulse>
                  Breaking
                </Badge>
              )}
              {category && (
                <Badge variant="outline" className="border-white/30 text-white bg-white/10">
                  {category.label}
                </Badge>
              )}
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="heading-display text-3xl sm:text-4xl md:text-5xl text-white mb-6"
            >
              {article.headline}
            </motion.h1>

            {/* Summary */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-lg text-white/80 mb-8"
            >
              {article.summary}
            </motion.p>

            {/* Meta */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-wrap items-center gap-6 text-sm text-white/70"
            >
              <span>{formattedDate}</span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                {article.readTime} min read
              </span>
              <span className="flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4" />
                {article.sources.length} sources
              </span>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Main content */}
      <section className="container-wide -mt-20 relative z-10">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Article body */}
          <div className="lg:col-span-2">
            <GlassCard padding="lg" className="mb-8">
              {/* Actions bar */}
              <div className="flex items-center justify-between pb-6 mb-6 border-b border-[var(--color-border-glass)]">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" icon={<Share2 className="w-4 h-4" />}>
                    Share
                  </Button>
                  <Button variant="ghost" size="sm" icon={<Bookmark className="w-4 h-4" />}>
                    Save
                  </Button>
                </div>
                <div className="text-sm text-[var(--color-text-muted)]">
                  Updated {new Date(article.updatedAt).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                </div>
              </div>

              {/* Article content */}
              <div className="body-text text-[var(--color-text-secondary)] space-y-6">
                {article.content.split('\n\n').map((paragraph, i) => (
                  <motion.p
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 + i * 0.05 }}
                  >
                    {paragraph}
                  </motion.p>
                ))}
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t border-[var(--color-border-glass)]">
                {article.tags.map((tag) => (
                  <a
                    key={tag}
                    href={`/tag/${tag}`}
                    className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] bg-[var(--color-surface-tertiary)] rounded-full hover:bg-[var(--color-surface-glass-hover)] transition-colors"
                  >
                    #{tag}
                  </a>
                ))}
              </div>
            </GlassCard>

            {/* Sources section */}
            <GlassCard padding="lg">
              <SourceList sources={article.sources} />
            </GlassCard>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Bias distribution card */}
            <GlassCard padding="md">
              <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-4">
                Source Distribution
              </h3>
              <p className="text-sm text-[var(--color-text-secondary)] mb-4">
                This story aggregates {article.sources.length} sources across the political spectrum.
              </p>
              <BiasSpectrum distribution={article.biasDistribution} size="lg" />

              <div className="grid grid-cols-5 gap-2 mt-6 text-center">
                {[
                  { label: 'Left', value: article.biasDistribution.left },
                  { label: 'Lean L', value: article.biasDistribution.leanLeft },
                  { label: 'Center', value: article.biasDistribution.center },
                  { label: 'Lean R', value: article.biasDistribution.leanRight },
                  { label: 'Right', value: article.biasDistribution.right },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="text-lg font-bold text-[var(--color-text-primary)]">
                      {item.value}%
                    </div>
                    <div className="text-xs text-[var(--color-text-muted)]">{item.label}</div>
                  </div>
                ))}
              </div>
            </GlassCard>

            {/* Related stories */}
            {relatedArticles.length > 0 && (
              <GlassCard padding="md">
                <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-4">
                  Related Stories
                </h3>
                <div className="space-y-4">
                  {relatedArticles.map((relatedArticle, i) => (
                    <a
                      key={relatedArticle.id}
                      href={`/article/${relatedArticle.slug}`}
                      className="block group"
                    >
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex gap-3"
                      >
                        <img
                          src={relatedArticle.imageUrl}
                          alt=""
                          className="w-16 h-16 rounded-[var(--radius-sm)] object-cover shrink-0"
                        />
                        <div>
                          <h4 className="text-sm font-medium text-[var(--color-text-primary)] line-clamp-2 group-hover:text-[var(--color-accent-pulse)] transition-colors">
                            {relatedArticle.headline}
                          </h4>
                          <span className="text-xs text-[var(--color-text-muted)] mt-1">
                            {relatedArticle.sources.length} sources
                          </span>
                        </div>
                      </motion.div>
                    </a>
                  ))}
                </div>
              </GlassCard>
            )}

            {/* Newsletter CTA */}
            <GlassCard padding="md" className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 rounded-full bg-[var(--color-accent-pulse-soft)] blur-2xl" />
              <div className="relative">
                <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-2">
                  Stay Informed
                </h3>
                <p className="text-sm text-[var(--color-text-secondary)] mb-4">
                  Get stories like this delivered to your inbox with full source analysis.
                </p>
                <input
                  type="email"
                  placeholder="Your email"
                  className="w-full px-3 py-2 mb-3 text-sm bg-[var(--color-surface-tertiary)] border border-[var(--color-border-glass)] rounded-[var(--radius-md)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent-pulse)]"
                />
                <Button variant="primary" size="sm" className="w-full">
                  Subscribe
                </Button>
              </div>
            </GlassCard>
          </div>
        </div>
      </section>

      {/* More from category */}
      <section className="container-wide py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex items-end justify-between mb-8"
        >
          <div>
            <h2 className="heading-display text-2xl md:text-3xl text-[var(--color-text-primary)] mb-2">
              More in {category?.label}
            </h2>
            <p className="text-[var(--color-text-secondary)]">
              Continue exploring stories from this topic
            </p>
          </div>
          <Button variant="ghost" size="sm">
            View all
          </Button>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockArticles
            .filter((a) => a.id !== article.id)
            .slice(0, 3)
            .map((a, i) => (
              <ArticleCard key={a.id} article={a} index={i} />
            ))}
        </div>
      </section>
    </article>
  )
}
