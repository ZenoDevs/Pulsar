import { useState } from 'react'
import { mockArticles } from '@/lib/data'
import type { Category } from '@/types'
import {
  FeaturedSection,
  ArticleList,
  TrendingTopics,
} from '@/components/home'

export function HomePage() {
  const [selectedCategory, setSelectedCategory] = useState<Category | 'all'>('all')

  const filteredArticles = mockArticles.filter((article) => {
    return selectedCategory === 'all' || article.category === selectedCategory
  })

  return (
    <div className="py-4 md:py-12">
      <div className="container-wide">
        <FeaturedSection />

        <ArticleList
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          articles={filteredArticles}
        />

        <TrendingTopics />
      </div>
    </div>
  )
}
