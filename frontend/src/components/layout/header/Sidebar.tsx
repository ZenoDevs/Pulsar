import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Search, X, ChevronDown } from 'lucide-react'
import { Logo, ThemeToggle, Button } from '@/components/ui'
import { categories } from '@/lib/data'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <AnimatePresence>
      {isOpen && <SidebarContent onClose={onClose} />}
    </AnimatePresence>
  )
}

function SidebarContent({ onClose }: { onClose: () => void }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isTopicsOpen, setIsTopicsOpen] = useState(false)

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

      {/* Sidebar Panel */}
      <motion.nav
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="absolute left-0 top-0 bottom-0 w-75 bg-surface-primary border-r border-border-glass flex flex-col"
      >
        {/* Header with Logo, Theme and Close */}
        <SidebarHeader onClose={onClose} />

        {/* Search Bar */}
        <SidebarSearch 
          value={searchQuery} 
          onChange={setSearchQuery} 
        />

        {/* Auth Buttons */}
        <SidebarAuth />

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex flex-col gap-1">
            <SidebarLink href="/" label="Home" onClick={onClose} />
            
            {/* Topics Accordion */}
            <SidebarAccordion
              label="Topics"
              isOpen={isTopicsOpen}
              onToggle={() => setIsTopicsOpen(!isTopicsOpen)}
            >
              {categories.map((category) => (
                <a
                  key={category.id}
                  href={`/category/${category.id}`}
                  onClick={onClose}
                  className="block px-3 py-2 text-sm text-text-muted hover:text-text-primary rounded-md hover:bg-surface-tertiary transition-colors"
                >
                  {category.label}
                </a>
              ))}
            </SidebarAccordion>

            <SidebarLink href="/sources" label="Sources" onClick={onClose} />
            <SidebarLink href="/about" label="About" onClick={onClose} />
          </div>
        </div>
      </motion.nav>
    </motion.div>
  )
}

function SidebarHeader({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex items-center justify-between p-4 border-b border-border-glass">
      <Logo size="sm" />
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <button
          onClick={onClose}
          className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-tertiary transition-colors"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}

function SidebarSearch({ 
  value, 
  onChange 
}: { 
  value: string
  onChange: (value: string) => void 
}) {
  return (
    <div className="p-4 border-b border-border-glass">
      <div className="flex items-center gap-2 px-3 py-2.5 bg-surface-tertiary rounded-md">
        <Search className="w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />
      </div>
    </div>
  )
}

function SidebarAuth() {
  return (
    <div className="p-4 border-b border-border-glass flex gap-2">
      <Button variant="ghost" size="sm" className="flex-1">
        Login
      </Button>
      <Button variant="primary" size="sm" className="flex-1">
        Subscribe
      </Button>
    </div>
  )
}

function SidebarLink({
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
      className="block px-3 py-2.5 text-text-secondary hover:text-text-primary rounded-md hover:bg-surface-tertiary transition-colors"
    >
      {label}
    </a>
  )
}

function SidebarAccordion({
  label,
  isOpen,
  onToggle,
  children,
}: {
  label: string
  isOpen: boolean
  onToggle: () => void
  children: React.ReactNode
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2.5 text-text-secondary hover:text-text-primary rounded-md hover:bg-surface-tertiary transition-colors"
      >
        <span>{label}</span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="pl-4 border-l-2 border-border-primary ml-3 mt-1 flex flex-col gap-0.5">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
