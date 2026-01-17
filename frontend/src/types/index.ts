export type BiasRating = 'left' | 'lean-left' | 'center' | 'lean-right' | 'right'

export interface Source {
  id: string
  name: string
  logo?: string
  url: string
  bias: BiasRating
  reliability: number // 0-100
  country: string
}

export interface ArticleSource {
  source: Source
  url: string
  title: string
  publishedAt: string
  excerpt: string
}

export interface Article {
  id: string
  slug: string
  headline: string
  summary: string
  content: string
  category: Category
  imageUrl: string
  imageAlt: string
  publishedAt: string
  updatedAt: string
  readTime: number
  sources: ArticleSource[]
  biasDistribution: {
    left: number
    leanLeft: number
    center: number
    leanRight: number
    right: number
  }
  tags: string[]
  isBreaking?: boolean
  isFeatured?: boolean
}

export type Category =
  | 'politics'
  | 'world'
  | 'technology'
  | 'science'
  | 'business'
  | 'health'
  | 'environment'
  | 'culture'

export interface CategoryInfo {
  id: Category
  label: string
  description: string
  color: string
}

export type Theme = 'light' | 'dark' | 'system'
