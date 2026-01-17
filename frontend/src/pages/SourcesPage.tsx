import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Search, Shield, ExternalLink, Filter, ChevronDown } from 'lucide-react'
import { GlassCard, Button, BiasIndicator } from '@/components/ui'
import { sources, getBiasLabel } from '@/lib/data'
import type { BiasRating } from '@/types'

type SortOption = 'name' | 'reliability' | 'bias'

export function SourcesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedBias, setSelectedBias] = useState<BiasRating | 'all'>('all')
  const [sortBy, setSortBy] = useState<SortOption>('reliability')
  const [isFilterOpen, setIsFilterOpen] = useState(false)

  const biasOptions: (BiasRating | 'all')[] = ['all', 'left', 'lean-left', 'center', 'lean-right', 'right']

  const filteredSources = sources
    .filter((source) => {
      const matchesSearch = source.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesBias = selectedBias === 'all' || source.bias === selectedBias
      return matchesSearch && matchesBias
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'reliability':
          return b.reliability - a.reliability
        case 'bias':
          const biasOrder = ['left', 'lean-left', 'center', 'lean-right', 'right']
          return biasOrder.indexOf(a.bias) - biasOrder.indexOf(b.bias)
        default:
          return 0
      }
    })

  return (
    <div className="py-12 md:py-16">
      {/* Hero section */}
      <section className="container-wide mb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-3xl"
        >
          <h1 className="heading-display text-4xl md:text-5xl text-[var(--color-text-primary)] mb-6">
            Our Sources
          </h1>
          <p className="text-lg text-[var(--color-text-secondary)] mb-8">
            Transparency is at the heart of what we do. Explore all {sources.length} news sources
            we aggregate from, their political leanings, and reliability scores. Every source is
            independently rated using our transparent methodology.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6">
            {[
              { value: sources.length, label: 'Total Sources' },
              { value: Math.round(sources.reduce((acc, s) => acc + s.reliability, 0) / sources.length), label: 'Avg. Reliability' },
              { value: new Set(sources.map((s) => s.country)).size, label: 'Countries' },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
              >
                <GlassCard padding="md" className="text-center">
                  <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">
                    {stat.value}{stat.label === 'Avg. Reliability' && '%'}
                  </div>
                  <div className="text-sm text-[var(--color-text-muted)]">{stat.label}</div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Filters section */}
      <section className="container-wide mb-8">
        <GlassCard padding="md">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
              <input
                type="text"
                placeholder="Search sources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[var(--color-surface-tertiary)] border border-[var(--color-border-glass)] rounded-[var(--radius-md)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent-pulse)]"
              />
            </div>

            {/* Bias filter */}
            <div className="relative">
              <button
                onClick={() => setIsFilterOpen(!isFilterOpen)}
                className="flex items-center gap-2 px-4 py-2.5 bg-[var(--color-surface-tertiary)] border border-[var(--color-border-glass)] rounded-[var(--radius-md)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-glass-hover)] transition-colors"
              >
                <Filter className="w-4 h-4" />
                <span>
                  {selectedBias === 'all' ? 'All biases' : getBiasLabel(selectedBias)}
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {isFilterOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.96 }}
                    className="absolute top-full right-0 mt-2 py-2 min-w-[160px] glass-card rounded-[var(--radius-md)] z-10"
                  >
                    {biasOptions.map((bias) => (
                      <button
                        key={bias}
                        onClick={() => {
                          setSelectedBias(bias)
                          setIsFilterOpen(false)
                        }}
                        className={`w-full px-4 py-2 text-left text-sm transition-colors ${
                          selectedBias === bias
                            ? 'text-[var(--color-accent-pulse)] bg-[var(--color-accent-pulse-soft)]'
                            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
                        }`}
                      >
                        {bias === 'all' ? 'All biases' : getBiasLabel(bias)}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--color-text-muted)]">Sort by:</span>
              <div className="flex gap-1 p-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
                {(['reliability', 'name', 'bias'] as SortOption[]).map((option) => (
                  <button
                    key={option}
                    onClick={() => setSortBy(option)}
                    className={`px-3 py-1.5 text-sm rounded-[var(--radius-sm)] transition-colors ${
                      sortBy === option
                        ? 'bg-[var(--color-surface-glass)] text-[var(--color-text-primary)] shadow-sm'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
                    }`}
                  >
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>
      </section>

      {/* Sources grid */}
      <section className="container-wide">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredSources.map((source, i) => (
              <motion.div
                key={source.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.03, type: 'spring', stiffness: 100 }}
              >
                <GlassCard padding="md" className="h-full">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <h3 className="heading-sans text-lg text-[var(--color-text-primary)] mb-1">
                        {source.name}
                      </h3>
                      <span className="text-sm text-[var(--color-text-muted)]">
                        {source.country}
                      </span>
                    </div>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-[var(--radius-sm)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>

                  {/* Bias indicator */}
                  <div className="mb-4">
                    <BiasIndicator bias={source.bias} size="md" />
                  </div>

                  {/* Reliability score */}
                  <div className="flex items-center justify-between pt-4 border-t border-[var(--color-border-glass)]">
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-[var(--color-accent-trust)]" />
                      <span className="text-sm text-[var(--color-text-secondary)]">
                        Reliability Score
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 rounded-full bg-[var(--color-surface-tertiary)] overflow-hidden">
                        <motion.div
                          className="h-full rounded-full"
                          style={{
                            backgroundColor:
                              source.reliability >= 80
                                ? 'var(--color-accent-trust)'
                                : source.reliability >= 60
                                  ? 'var(--color-accent-warm)'
                                  : 'var(--color-bias-right)',
                          }}
                          initial={{ width: 0 }}
                          animate={{ width: `${source.reliability}%` }}
                          transition={{ delay: i * 0.03 + 0.2, duration: 0.5 }}
                        />
                      </div>
                      <span className="text-sm font-medium text-[var(--color-text-primary)] w-10">
                        {source.reliability}%
                      </span>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {filteredSources.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <p className="text-[var(--color-text-muted)] mb-4">
              No sources match your search criteria
            </p>
            <Button variant="secondary" onClick={() => {
              setSearchQuery('')
              setSelectedBias('all')
            }}>
              Clear filters
            </Button>
          </motion.div>
        )}
      </section>

      {/* Methodology section */}
      <section className="container-wide py-16 mt-16 border-t border-[var(--color-border-glass)]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center"
        >
          <h2 className="heading-display text-3xl text-[var(--color-text-primary)] mb-6">
            Our Methodology
          </h2>
          <p className="text-[var(--color-text-secondary)] mb-8">
            We rate sources based on factual accuracy, editorial standards, transparency about
            ownership and funding, and correction practices. Political bias is assessed through
            content analysis of story selection, framing, and editorial positions.
          </p>
          <Button variant="glass" size="lg">
            Read our full methodology
          </Button>
        </motion.div>
      </section>
    </div>
  )
}
