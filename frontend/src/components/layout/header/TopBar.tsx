import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Globe, ChevronDown } from 'lucide-react'

// Format current date in journal style
function formatDate() {
  const now = new Date()
  return now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const languages = [
  { code: 'EN', label: 'English' },
  { code: 'IT', label: 'Italiano' },
  { code: 'ES', label: 'Español' },
  { code: 'FR', label: 'Français' },
  { code: 'DE', label: 'Deutsch' },
]

export function TopBar() {
  const [selectedLanguage, setSelectedLanguage] = useState('EN')
  const [isLangOpen, setIsLangOpen] = useState(false)

  return (
    <div className="hidden lg:block bg-surface-secondary/50 border-b border-border-primary">
      <div className="container-wide">
        <div className="flex items-center justify-between h-8 text-xs text-text-muted">
          {/* Date */}
          <span>{formatDate()}</span>

          {/* Right side - Language Selector */}
          <div className="flex items-center">
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              isOpen={isLangOpen}
              onToggle={() => setIsLangOpen(!isLangOpen)}
              onSelect={(code) => {
                setSelectedLanguage(code)
                setIsLangOpen(false)
              }}
              onBlur={() => setTimeout(() => setIsLangOpen(false), 150)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function LanguageSelector({
  selectedLanguage,
  isOpen,
  onToggle,
  onSelect,
  onBlur,
}: {
  selectedLanguage: string
  isOpen: boolean
  onToggle: () => void
  onSelect: (code: string) => void
  onBlur: () => void
}) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        onBlur={onBlur}
        className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-surface-tertiary transition-colors"
      >
        <Globe className="w-3.5 h-3.5" />
        <span>{selectedLanguage}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden z-80 absolute right-0 top-full mt-1 py-1 min-w-28 bg-surface-secondary border border-border-primary rounded-md shadow-lg"
          >
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => onSelect(lang.code)}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-surface-tertiary transition-colors ${
                  selectedLanguage === lang.code ? 'text-accent-pulse' : 'text-text-secondary'
                }`}
              >
                {lang.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
