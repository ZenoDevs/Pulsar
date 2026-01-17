import { useState, useEffect } from 'react'
import { motion } from 'motion/react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { GlassCard } from '@/components/ui'
import { mockArticles, categories } from '@/lib/data'
import type { Category, Article } from '@/types'
import { CategoryPill } from './CategoryPill'
import { ArticleRow } from './ArticleRow'

const ARTICLES_PER_PAGE = 6

interface ArticleListProps {
  selectedCategory: Category | 'all'
  onCategoryChange: (category: Category | 'all') => void
  articles: Article[]
}

export function ArticleList({ selectedCategory, onCategoryChange, articles }: ArticleListProps) {
  const [currentPage, setCurrentPage] = useState(1)
  
  // Reset to page 1 when category or articles change
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedCategory, articles.length])

  const totalPages = Math.ceil(articles.length / ARTICLES_PER_PAGE)
  const startIndex = (currentPage - 1) * ARTICLES_PER_PAGE
  const paginatedArticles = articles.slice(startIndex, startIndex + ARTICLES_PER_PAGE)

  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4 }}
      className="mb-6"
    >
      <h2 className="heading-sans text-xl text-[var(--color-text-primary)] mb-4">All Articles</h2>
      <GlassCard padding="none" hover={false}>
        {/* Category Filters */}
        <div className="flex items-center gap-2 overflow-x-auto p-4 md:px-6 border-b border-[var(--color-border-glass)] scrollbar-hide">
          <CategoryPill
            label="All"
            isActive={selectedCategory === 'all'}
            onClick={() => onCategoryChange('all')}
            count={mockArticles.length}
          />
          {categories.map((cat) => (
            <CategoryPill
              key={cat.id}
              label={cat.label}
              isActive={selectedCategory === cat.id}
              onClick={() => onCategoryChange(cat.id)}
              count={mockArticles.filter((a) => a.category === cat.id).length}
            />
          ))}
        </div>

        {/* Table Header */}
        <div className="hidden md:grid md:grid-cols-12 gap-4 px-6 py-3 border-b border-[var(--color-border-glass)] text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
          <div className="col-span-6">Story</div>
          <div className="col-span-2">Category</div>
          <div className="col-span-2">Sources</div>
          <div className="col-span-2 text-right">Time</div>
        </div>

        {/* Articles List */}
        <div className="divide-y divide-[var(--color-border-glass)]">
          {paginatedArticles.map((article, index) => (
            <ArticleRow key={article.id} article={article} index={index} />
          ))}
        </div>

        {articles.length === 0 && (
          <div className="py-16 text-center">
            <p className="text-[var(--color-text-muted)]">
              No stories found matching your criteria
            </p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--color-border-glass)]">
            <span className="text-sm text-[var(--color-text-muted)]">
              Showing {startIndex + 1}-{Math.min(startIndex + ARTICLES_PER_PAGE, articles.length)} of {articles.length}
            </span>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`
                      min-w-[32px] h-8 rounded-lg text-sm font-medium transition-colors
                      ${currentPage === page
                        ? 'bg-[var(--color-text-primary)] text-[var(--color-surface-primary)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
                      }
                    `}
                  >
                    {page}
                  </button>
                ))}
              </div>
              
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </GlassCard>
    </motion.section>
  )
}
