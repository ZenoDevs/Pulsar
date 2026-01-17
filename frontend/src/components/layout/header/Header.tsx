import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { Logo, ThemeToggle, Button } from '@/components/ui'
import { TopBar } from './TopBar'
import { TrendingBar } from './TrendingBar'
import { Sidebar } from './Sidebar'
import { SearchBar } from './SearchBar'

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 32)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      {/* Top Bar - Date & Language (NOT sticky) */}
      <TopBar />

      {/* Sticky Header (Navbar + Trending) */}
      <header
        className={`
          sticky top-0 left-0 right-0 z-50
          transition-all duration-300
          ${isScrolled
            ? 'bg-surface-glass backdrop-blur-glass shadow-sm'
            : 'bg-transparent'
          }
        `}
      >
        {/* Main Navbar */}
        <div className="border-b border-border-primary">
          <div className="container-wide">
            <div className="flex items-center justify-between h-14 sm:h-16">
              {/* Left - Menu button + Logo */}
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="p-2 rounded-md cursor-pointer text-text-secondary hover:text-text-primary hover:bg-surface-tertiary transition-colors"
                  aria-label="Toggle menu"
                >
                  <Menu className="w-5 h-5" />
                </button>

                <Logo size="md" className="hidden sm:flex" />
                <Logo size="sm" className="flex sm:hidden" />
              </div>

              {/* Right - Search, Theme & Auth */}
              <div className="flex items-center gap-2">
                <SearchBar
                  value={searchQuery}
                  onChange={setSearchQuery}
                  isExpanded={isSearchExpanded}
                  onExpandChange={setIsSearchExpanded}
                />

                <div className="hidden sm:block">
                  <ThemeToggle />
                </div>

                <Button variant="ghost" size="sm" className="hidden md:flex">
                  Login
                </Button>

                <Button variant="primary" size="sm" className="hidden md:flex">
                  Subscribe
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Trending Now Bar */}
        <TrendingBar />
      </header>

      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)} 
      />
    </>
  )
}
