import type { ReactNode } from 'react'
import { Header } from './header'
import { Footer } from './Footer'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Animated gradient background */}
      <div className="gradient-bg">
        <div className="gradient-blob-3" />
      </div>

      {/* Noise overlay */}
      <div className="fixed inset-0 pointer-events-none noise z-1" />

      <Header />

      <main className="flex-1 relative z-10">
        {children}
      </main>

      <Footer />
    </div>
  )
}
