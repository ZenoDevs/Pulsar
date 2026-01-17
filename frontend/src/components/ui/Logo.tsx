interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Logo({ size = 'md', className = '' }: LogoProps) {
  const sizes = {
    sm: { height: 24, width: 120 },
    md: { height: 32, width: 160 },
    lg: { height: 44, width: 220 },
  }

  const { height, width } = sizes[size]

  return (
    <a
      href="/"
      className={`flex items-center group ${className}`}
    >
      <svg
        width={width}
        height={height}
        viewBox="0 0 160 32"
        fill="none"
        className="transition-all duration-300"
      >
        <defs>
          <linearGradient id="wave-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-accent-pulse)" />
            <stop offset="100%" stopColor="var(--color-accent-trust)" />
          </linearGradient>
        </defs>

        {/* Signal waves - broadcasting from left */}
        <g className="group-hover:opacity-100 opacity-70 transition-opacity duration-300">
          {/* Inner wave */}
          <path
            d="M8 10 Q2 16, 8 22"
            stroke="var(--color-accent-pulse)"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            className="group-hover:stroke-[var(--color-accent-pulse)]"
          />
          {/* Middle wave */}
          <path
            d="M14 6 Q4 16, 14 26"
            stroke="url(#wave-gradient)"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            opacity="0.7"
          />
          {/* Outer wave */}
          <path
            d="M20 2 Q6 16, 20 30"
            stroke="var(--color-accent-trust)"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            opacity="0.4"
          />
        </g>

        {/* Core dot - the source */}
        <circle
          cx="10"
          cy="16"
          r="2.5"
          fill="var(--color-accent-pulse)"
          className="group-hover:fill-[var(--color-accent-pulse)]"
        />

        {/* PULSAR text */}
        <text
          x="32"
          y="22"
          fill="var(--color-text-primary)"
          fontFamily="ui-serif, Georgia, Cambria, serif"
          fontSize="20"
          fontWeight="500"
          letterSpacing="0.08em"
          className="transition-colors duration-300"
        >
          PULSAR
        </text>

        {/* Subtle underline accent */}
        <line
          x1="32"
          y1="26"
          x2="130"
          y2="26"
          stroke="var(--color-text-primary)"
          strokeWidth="0.5"
          opacity="0.2"
          className="group-hover:opacity-40 transition-opacity duration-300"
        />
      </svg>
    </a>
  )
}
