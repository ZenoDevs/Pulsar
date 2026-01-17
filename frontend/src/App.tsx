import { useState, useEffect } from 'react'
import { ThemeProvider } from '@/context/ThemeContext'
import { Layout } from '@/components/layout'
import { HomePage, ArticlePage, SourcesPage } from '@/pages'

type Route = 'home' | 'article' | 'sources' | 'about'

function getRouteFromPath(): { route: Route; slug?: string } {
  const path = window.location.pathname

  if (path.startsWith('/article/')) {
    const slug = path.replace('/article/', '')
    return { route: 'article', slug }
  }

  if (path === '/sources') {
    return { route: 'sources' }
  }

  if (path === '/about') {
    return { route: 'about' }
  }

  return { route: 'home' }
}

function Router() {
  const [routeInfo, setRouteInfo] = useState(getRouteFromPath)

  useEffect(() => {
    const handlePopState = () => {
      setRouteInfo(getRouteFromPath())
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // Handle link clicks for client-side routing
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const anchor = target.closest('a')

      if (
        anchor &&
        anchor.href &&
        anchor.href.startsWith(window.location.origin) &&
        !anchor.hasAttribute('target')
      ) {
        e.preventDefault()
        const url = new URL(anchor.href)
        window.history.pushState({}, '', url.pathname)
        setRouteInfo(getRouteFromPath())
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    }

    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  const { route, slug } = routeInfo

  return (
    <Layout>
      {route === 'home' && <HomePage />}
      {route === 'article' && <ArticlePage slug={slug} />}
      {route === 'sources' && <SourcesPage />}
      {route === 'about' && <AboutPage />}
    </Layout>
  )
}

function AboutPage() {
  return (
    <div className="container-narrow py-16">
      <h1 className="heading-display text-4xl md:text-5xl text-[var(--color-text-primary)] mb-6">
        About Pulsar
      </h1>
      <div className="body-text text-[var(--color-text-secondary)] space-y-6">
        <p>
          Pulsar was founded on a simple belief: in an era of information overload and increasing
          polarization, what people need most is transparency, not curation.
        </p>
        <p>
          We aggregate news from hundreds of sources across the political spectrum, presenting
          every story with full visibility into its sources, their biases, and our methodology.
          We don't tell you what to think—we give you the tools to think for yourself.
        </p>
        <p>
          Our name comes from pulsars, the rapidly rotating neutron stars that emit beams of
          electromagnetic radiation. Like these cosmic lighthouses, we aim to be a consistent,
          reliable beacon cutting through the darkness of misinformation and bias.
        </p>
        <h2 className="heading-sans text-2xl text-[var(--color-text-primary)] pt-4">
          Our Principles
        </h2>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Transparency First:</strong> Every piece of content comes with full source
            attribution and bias analysis.
          </li>
          <li>
            <strong>Multiple Perspectives:</strong> We believe understanding requires seeing all
            sides of a story.
          </li>
          <li>
            <strong>Reader Autonomy:</strong> We provide information; you draw conclusions.
          </li>
          <li>
            <strong>Continuous Improvement:</strong> Our methodology evolves with feedback and
            new research.
          </li>
        </ul>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <Router />
    </ThemeProvider>
  )
}
