import { TrendingUp } from 'lucide-react'

// Fake trending topics - will be replaced with real data
const trendingTopics = [
  { id: 1, label: 'Climate Summit 2026' },
  { id: 2, label: 'AI Regulation' },
  { id: 3, label: 'Fed Interest Rates' },
  { id: 4, label: 'Tech Layoffs' },
  { id: 5, label: 'EU Elections' },
  { id: 6, label: 'Space X Launch' },
  { id: 7, label: 'Cybersecurity' },
]

export function TrendingBar() {
  return (
    <div className="border-b border-border-primary">
      <div className="container-wide overflow-x-auto scrollbar-hide">
        <div className="flex items-center lg:justify-center gap-2 h-11 min-w-max px-1">
          {/* Trending badge/label - hidden on mobile for space */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-accent-pulse-vivid border-r border-border-primary pr-3 mr-1 shrink-0">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Trending</span>
          </div>
          
          {trendingTopics.map((topic) => (
            <TrendingBadge key={topic.id} topic={topic} />
          ))}
        </div>
      </div>
    </div>
  )
}

function TrendingBadge({ topic }: { topic: { id: number; label: string } }) {
  return (
    <a
      href={`/search?q=${encodeURIComponent(topic.label)}`}
      className="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full border transition-all whitespace-nowrap shrink-0 bg-surface-tertiary border-border-primary text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
    >
      {topic.label}
    </a>
  )
}
