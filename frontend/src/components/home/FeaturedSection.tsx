import { motion } from 'motion/react'
import { mockArticles } from '@/lib/data'
import { HeroArticle } from './HeroArticle'
import { FeaturedCard } from './FeaturedCard'

export function FeaturedSection() {
  const featuredArticles = mockArticles.filter((a) => a.isFeatured)
  const heroArticle = featuredArticles[0]
  const secondaryArticles = featuredArticles.slice(1, 3)
  const tertiaryArticles = mockArticles.filter((a) => !a.isFeatured).slice(0, 2)

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="mb-16"
    >
      {/* Main Grid - Bento style */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6">
        {/* Hero Article - Large */}
        {heroArticle && <HeroArticle article={heroArticle} />}

        {/* Secondary Articles - Stacked */}
        <div className="lg:col-span-5 flex flex-col gap-4 md:gap-6">
          {secondaryArticles.map((article, i) => (
            <FeaturedCard key={article.id} article={article} index={i} />
          ))}
        </div>
      </div>

      {/* Tertiary Row */}
      {tertiaryArticles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mt-4 md:mt-6">
          {tertiaryArticles.map((article, i) => (
            <FeaturedCard key={article.id} article={article} index={i + 2} variant="horizontal" />
          ))}
        </div>
      )}
    </motion.section>
  )
}
