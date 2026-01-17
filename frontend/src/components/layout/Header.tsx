import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Search, Menu, X, ChevronDown } from 'lucide-react'
import { Logo, ThemeToggle, Button } from '@/components/ui'
import { categories } from '@/lib/data'

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      <header
        className={`
          fixed top-0 left-0 right-0 z-50
          transition-all duration-300
          border-b
          ${isScrolled
            ? 'bg-[var(--color-surface-glass)] backdrop-blur-[20px] border-[var(--color-border-glass)]'
            : 'bg-transparent border-transparent'
          }
        `}
      >
        <div className="container-wide relative">
          <div className="flex items-center justify-between h-14 sm:h-16 md:h-20">
            {/* Menu button + Logo + Navigation */}
            <div className="flex items-center gap-5">
              {/* Menu button - always visible */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 sm:p-2.5 rounded-[var(--radius-md)] cursor-pointer text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-tertiary)] z-70 transition-colors"
                aria-label="Toggle menu"
              >
                <Menu className="w-5 h-5" />
              </button>

              <Logo size="md" className="hidden sm:flex" />
              <Logo size="sm" className="flex sm:hidden" />

              {/* Desktop Navigation */}
              <nav className="hidden lg:flex items-center gap-1 ml-6">
                <NavLink href="/" label="Home" />
                <NavDropdown label="Topics" items={categories.map(c => ({ href: `/category/${c.id}`, label: c.label }))} />
                <NavLink href="/sources" label="Sources" />
                <NavLink href="/about" label="About" />
              </nav>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 sm:gap-2">
              {/* Expandable Search Bar */}
              <motion.div
                initial={false}
                animate={{ width: isSearchExpanded ? 280 : 160 }}
                transition={{ duration: 0.10, ease: 'easeInOut' }}
                className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-full bg-[var(--color-surface-tertiary)] focus-within:ring-2 focus-within:ring-[var(--color-accent-pulse)]/30 focus-within:bg-[var(--color-surface-secondary)] transition-all"
              >
                <Search className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                <input
                  type="text"
                  id="header-search"
                  placeholder={isSearchExpanded ? "Search stories, topics..." : "Search..."}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setIsSearchExpanded(true)}
                  onBlur={() => {
                    if (!searchQuery) setIsSearchExpanded(false)
                  }}
                  style={{ outline: 'none', boxShadow: 'none' }}
                  className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] border-none min-w-0 focus:outline-none focus:ring-0 focus:border-none focus:shadow-none"
                />
                {isSearchExpanded && searchQuery && (
                  <button
                    onClick={() => {
                      setSearchQuery('')
                      setIsSearchExpanded(false)
                    }}
                    className="p-0.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </motion.div>

              {/* Theme toggle - hidden on mobile, available in sidebar */}
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
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <MobileMenu onClose={() => setIsMobileMenuOpen(false)} />
        )}
      </AnimatePresence>
    </>
  )
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-[var(--radius-md)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
    >
      {label}
    </a>
  )
}

function NavDropdown({ label, items }: { label: string; items: { href: string; label: string }[] }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-[var(--radius-md)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
      >
        {label}
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            className="absolute top-full left-0 mt-1 py-2 min-w-[180px] glass-card rounded-[var(--radius-md)] overflow-hidden"
          >
            {items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="block px-4 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
              >
                {item.label}
              </a>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MobileMenu({ onClose }: { onClose: () => void }) {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed inset-0 z-60"
    >
      {/* Blur layer */}
      <div 
        className="absolute inset-0 backdrop-blur-sm transition-[backdrop-filter] duration-300"
        style={{ WebkitBackdropFilter: 'blur(8px)' }}
      />
      {/* Dark overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      <motion.nav
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="absolute left-0 top-0 bottom-0 w-[300px] bg-[var(--color-surface-primary)] border-r border-[var(--color-border-glass)] flex flex-col"
      >
        {/* Header with Logo, Theme and Close */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border-glass)]">
          <Logo size="sm" />
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              onClick={onClose}
              className="p-2 rounded-[var(--radius-md)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-[var(--color-border-glass)]">
          <div className="flex items-center gap-2 px-3 py-2.5 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
            <Search className="w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
            />
          </div>
        </div>

        {/* Auth Buttons */}
        <div className="p-4 border-b border-[var(--color-border-glass)] flex gap-2">
          <Button variant="ghost" size="sm" className="flex-1">
            Login
          </Button>
          <Button variant="primary" size="sm" className="flex-1">
            Subscribe
          </Button>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-col gap-1">
            <MobileNavLink href="/" label="Home" onClick={onClose} />
            <MobileNavLink href="/sources" label="Sources" onClick={onClose} />
            <MobileNavLink href="/about" label="About" onClick={onClose} />
          </div>

          <div className="border-t border-[var(--color-border-primary)] my-4 pt-4">
            <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-2 px-3">
              Topics
            </p>
            {categories.map((category) => (
              <MobileNavLink
                key={category.id}
                href={`/category/${category.id}`}
                label={category.label}
                onClick={onClose}
              />
            ))}
          </div>
        </div>

      </motion.nav>
    </motion.div>
  )
}

function MobileNavLink({
  href,
  label,
  onClick,
}: {
  href: string
  label: string
  onClick: () => void
}) {
  return (
    <a
      href={href}
      onClick={onClick}
      className="block px-3 py-2.5 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-[var(--radius-md)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
    >
      {label}
    </a>
  )
}

function SearchModal({ onClose }: { onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-md"
        onClick={onClose}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: -20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -20 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        className="relative w-full max-w-2xl mx-4 glass-card p-2"
      >
        <div className="flex items-center gap-3 px-4">
          <Search className="w-5 h-5 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search stories, topics, sources..."
            className="flex-1 py-4 bg-transparent text-lg text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
            autoFocus
          />
          <kbd className="hidden sm:flex items-center gap-1 px-2 py-1 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-tertiary)] rounded">
            ESC
          </kbd>
        </div>

        <div className="border-t border-[var(--color-border-glass)] mt-2 pt-4 px-4 pb-2">
          <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
            Popular searches
          </p>
          <div className="flex flex-wrap gap-2">
            {['Climate Summit', 'AI Healthcare', 'Economy', 'Space Exploration'].map((term) => (
              <button
                key={term}
                className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] bg-[var(--color-surface-tertiary)] rounded-full hover:bg-[var(--color-surface-glass-hover)] transition-colors"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
