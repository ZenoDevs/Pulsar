import { motion } from 'motion/react'
import { Logo, ThemeToggle } from '@/components/ui'
import { Github, Twitter, Linkedin, Mail } from 'lucide-react'
import { categories } from '@/lib/data'

export function Footer() {
  const currentYear = new Date().getFullYear()

  const socialLinks = [
    { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
    { icon: Github, href: 'https://github.com', label: 'GitHub' },
    { icon: Linkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
    { icon: Mail, href: 'mailto:hello@pulsar.news', label: 'Email' },
  ]

  return (
    <footer className="relative mt-24 border-t border-[var(--color-border-glass)]">
      {/* Gradient background */}
      <div className="absolute inset-0 gradient-bg opacity-30 pointer-events-none" />

      <div className="container-wide relative py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8">
          {/* Brand column */}
          <div className="lg:col-span-1">
            <Logo size="lg" className="mb-6" />
            <p className="text-[var(--color-text-secondary)] text-sm leading-relaxed mb-6 max-w-xs">
              Transparent news aggregation. See all perspectives, understand the full story.
              Truth through transparency.
            </p>
            <div className="flex items-center gap-3">
              {socialLinks.map(({ icon: Icon, href, label }) => (
                <motion.a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2.5 rounded-[var(--radius-md)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] bg-[var(--color-surface-tertiary)] hover:bg-[var(--color-surface-glass)] transition-colors"
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label={label}
                >
                  <Icon className="w-4 h-4" />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Topics column */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider mb-4">
              Topics
            </h3>
            <ul className="space-y-3">
              {categories.slice(0, 6).map((category) => (
                <li key={category.id}>
                  <a
                    href={`/category/${category.id}`}
                    className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                  >
                    {category.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company column */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider mb-4">
              Company
            </h3>
            <ul className="space-y-3">
              {[
                { label: 'About Us', href: '/about' },
                { label: 'Our Sources', href: '/sources' },
                { label: 'Methodology', href: '/methodology' },
                { label: 'Careers', href: '/careers' },
                { label: 'Press Kit', href: '/press' },
                { label: 'Contact', href: '/contact' },
              ].map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter column */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider mb-4">
              Stay Informed
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-4">
              Get the day's most important stories with full perspective analysis.
            </p>
            <form className="space-y-3">
              <div className="relative">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="w-full px-4 py-3 text-sm bg-[var(--color-surface-glass)] backdrop-blur-[var(--blur-glass)] border border-[var(--color-border-glass)] rounded-[var(--radius-md)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent-pulse)]"
                />
              </div>
              <motion.button
                type="submit"
                className="w-full px-4 py-3 text-sm font-medium bg-[var(--color-text-primary)] text-[var(--color-surface-primary)] rounded-[var(--radius-md)] hover:opacity-90 transition-opacity"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Subscribe
              </motion.button>
            </form>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-16 pt-8 border-t border-[var(--color-border-glass)]">
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-[var(--color-text-muted)]">
            <span>&copy; {currentYear} Pulsar News</span>
            <a href="/privacy" className="hover:text-[var(--color-text-secondary)] transition-colors">
              Privacy Policy
            </a>
            <a href="/terms" className="hover:text-[var(--color-text-secondary)] transition-colors">
              Terms of Service
            </a>
            <a href="/cookies" className="hover:text-[var(--color-text-secondary)] transition-colors">
              Cookie Policy
            </a>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs text-[var(--color-text-muted)]">Theme</span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  )
}
