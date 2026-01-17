import type { Article, Source, CategoryInfo } from '@/types'

export const sources: Source[] = [
  {
    id: 'nyt',
    name: 'The New York Times',
    url: 'https://nytimes.com',
    bias: 'lean-left',
    reliability: 85,
    country: 'US',
  },
  {
    id: 'wsj',
    name: 'The Wall Street Journal',
    url: 'https://wsj.com',
    bias: 'lean-right',
    reliability: 88,
    country: 'US',
  },
  {
    id: 'bbc',
    name: 'BBC News',
    url: 'https://bbc.com',
    bias: 'center',
    reliability: 90,
    country: 'UK',
  },
  {
    id: 'reuters',
    name: 'Reuters',
    url: 'https://reuters.com',
    bias: 'center',
    reliability: 94,
    country: 'UK',
  },
  {
    id: 'ap',
    name: 'Associated Press',
    url: 'https://apnews.com',
    bias: 'center',
    reliability: 93,
    country: 'US',
  },
  {
    id: 'guardian',
    name: 'The Guardian',
    url: 'https://theguardian.com',
    bias: 'left',
    reliability: 82,
    country: 'UK',
  },
  {
    id: 'fox',
    name: 'Fox News',
    url: 'https://foxnews.com',
    bias: 'right',
    reliability: 65,
    country: 'US',
  },
  {
    id: 'economist',
    name: 'The Economist',
    url: 'https://economist.com',
    bias: 'lean-right',
    reliability: 89,
    country: 'UK',
  },
]

export const categories: CategoryInfo[] = [
  { id: 'politics', label: 'Politics', description: 'Government, policy, and political affairs', color: 'var(--color-accent-pulse)' },
  { id: 'world', label: 'World', description: 'International news and global events', color: 'var(--color-accent-trust)' },
  { id: 'technology', label: 'Technology', description: 'Tech industry, innovation, and digital trends', color: 'var(--color-accent-warm)' },
  { id: 'science', label: 'Science', description: 'Scientific discoveries and research', color: 'var(--color-bias-center)' },
  { id: 'business', label: 'Business', description: 'Markets, economy, and corporate news', color: 'var(--color-bias-right)' },
  { id: 'health', label: 'Health', description: 'Healthcare, medicine, and wellness', color: 'var(--color-accent-trust)' },
  { id: 'environment', label: 'Environment', description: 'Climate, nature, and sustainability', color: 'var(--color-bias-center)' },
  { id: 'culture', label: 'Culture', description: 'Arts, entertainment, and society', color: 'var(--color-accent-pulse)' },
]

export const mockArticles: Article[] = [
  {
    id: '1',
    slug: 'global-climate-summit-reaches-historic-agreement',
    headline: 'Global Climate Summit Reaches Historic Agreement on Carbon Emissions',
    summary: 'World leaders convene to establish unprecedented carbon reduction targets, marking a pivotal moment in international climate policy. The agreement sets binding commitments for 195 nations.',
    content: `In a landmark moment for international climate diplomacy, representatives from 195 nations have signed a comprehensive agreement establishing the most ambitious carbon reduction targets in history.

The accord, reached after two weeks of intensive negotiations at the Global Climate Summit, commits developed nations to achieving net-zero emissions by 2045—five years ahead of previous targets—while providing substantial financial support to developing countries transitioning to clean energy.

"This is the kind of decisive action our planet desperately needs," said UN Secretary-General in a statement following the agreement. "For the first time, we have binding commitments backed by concrete implementation mechanisms."

Key provisions of the agreement include:
- A global carbon pricing mechanism starting at $75 per ton
- $500 billion annual climate finance fund for developing nations
- Mandatory corporate emissions reporting standards
- Accelerated phase-out of coal power by 2035

The agreement has been met with cautious optimism from environmental groups, though some argue the targets still fall short of what's needed to limit warming to 1.5°C.

Industry representatives expressed concerns about the economic impact of rapid decarbonization, while emphasizing their commitment to the transition. "The path forward requires collaboration between governments and the private sector," noted the head of the World Business Council.`,
    category: 'environment',
    imageUrl: 'https://images.unsplash.com/photo-1569163139599-0f4517e36f51?w=1200&h=800&fit=crop',
    imageAlt: 'World leaders at climate summit podium',
    publishedAt: '2025-01-15T09:30:00Z',
    updatedAt: '2025-01-15T14:22:00Z',
    readTime: 6,
    sources: [
      {
        source: sources[3], // Reuters
        url: 'https://reuters.com/article/climate-summit-agreement',
        title: 'Nations reach historic climate deal with binding carbon targets',
        publishedAt: '2025-01-15T08:45:00Z',
        excerpt: 'The agreement sets legally binding emissions reduction targets for developed nations...',
      },
      {
        source: sources[2], // BBC
        url: 'https://bbc.com/news/world-climate-summit',
        title: 'Climate Summit: What the new agreement means for the planet',
        publishedAt: '2025-01-15T09:00:00Z',
        excerpt: 'Experts weigh in on whether the ambitious targets go far enough...',
      },
      {
        source: sources[0], // NYT
        url: 'https://nytimes.com/2025/01/15/climate/summit-agreement.html',
        title: 'A New Chapter for Climate Action: Inside the Summit\'s Final Hours',
        publishedAt: '2025-01-15T10:15:00Z',
        excerpt: 'Negotiators worked through the night to bridge divides between developed and developing nations...',
      },
      {
        source: sources[1], // WSJ
        url: 'https://wsj.com/articles/climate-summit-business-impact',
        title: 'Climate Deal Sets Stage for Massive Corporate Restructuring',
        publishedAt: '2025-01-15T11:30:00Z',
        excerpt: 'Companies face significant compliance costs under new carbon pricing regime...',
      },
      {
        source: sources[5], // Guardian
        url: 'https://theguardian.com/environment/climate-summit-deal',
        title: 'Historic but not enough: Scientists react to climate summit outcome',
        publishedAt: '2025-01-15T10:00:00Z',
        excerpt: 'While celebrating the agreement, climate scientists warn more action is needed...',
      },
    ],
    biasDistribution: {
      left: 15,
      leanLeft: 25,
      center: 35,
      leanRight: 20,
      right: 5,
    },
    tags: ['climate', 'environment', 'international', 'policy'],
    isFeatured: true,
    isBreaking: true,
  },
  {
    id: '2',
    slug: 'ai-breakthrough-medical-diagnosis',
    headline: 'AI System Achieves Breakthrough in Early Cancer Detection',
    summary: 'A new artificial intelligence model developed by an international research consortium demonstrates 97% accuracy in detecting early-stage cancers, outperforming human specialists.',
    content: `An international team of researchers has unveiled an artificial intelligence system capable of detecting early-stage cancers with unprecedented accuracy, potentially revolutionizing diagnostic medicine.

The AI model, trained on millions of medical images from hospitals across 40 countries, achieved a 97.3% accuracy rate in identifying early-stage tumors—significantly outperforming the 89% average accuracy of human radiologists.

"This isn't about replacing doctors," explained the lead researcher. "It's about giving them a powerful tool that catches what human eyes might miss. Early detection saves lives."

The system has shown particular promise in detecting:
- Lung cancer from CT scans (96.8% accuracy)
- Breast cancer from mammograms (97.5% accuracy)
- Skin cancer from dermoscopic images (98.1% accuracy)

Clinical trials are now underway at 200 hospitals worldwide, with regulators in multiple countries expediting review processes for potential approval.

However, some medical professionals have raised concerns about over-reliance on AI systems and the importance of maintaining human oversight in diagnostic processes.`,
    category: 'health',
    imageUrl: 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1200&h=800&fit=crop',
    imageAlt: 'Medical AI diagnostic system display',
    publishedAt: '2025-01-14T15:00:00Z',
    updatedAt: '2025-01-14T18:30:00Z',
    readTime: 5,
    sources: [
      {
        source: sources[4], // AP
        url: 'https://apnews.com/article/ai-cancer-detection',
        title: 'AI system shows promise in early cancer detection',
        publishedAt: '2025-01-14T14:00:00Z',
        excerpt: 'The breakthrough could transform how doctors diagnose cancer...',
      },
      {
        source: sources[2], // BBC
        url: 'https://bbc.com/news/health-ai-diagnosis',
        title: 'Revolutionary AI detects cancer earlier than doctors',
        publishedAt: '2025-01-14T15:30:00Z',
        excerpt: 'Medical experts hail the development as a potential game-changer...',
      },
      {
        source: sources[7], // Economist
        url: 'https://economist.com/science/ai-healthcare-future',
        title: 'The economics of AI in healthcare: Promise and pitfalls',
        publishedAt: '2025-01-14T16:00:00Z',
        excerpt: 'While promising, the technology raises questions about healthcare costs and access...',
      },
    ],
    biasDistribution: {
      left: 10,
      leanLeft: 20,
      center: 50,
      leanRight: 15,
      right: 5,
    },
    tags: ['AI', 'healthcare', 'technology', 'medicine'],
    isFeatured: true,
  },
  {
    id: '3',
    slug: 'central-bank-interest-rate-decision',
    headline: 'Federal Reserve Signals Shift in Monetary Policy Approach',
    summary: 'Central bank announces new framework for interest rate decisions, emphasizing employment alongside inflation targets in a departure from recent policy.',
    content: `The Federal Reserve announced a significant shift in its monetary policy approach, signaling that future interest rate decisions will place greater emphasis on employment metrics alongside traditional inflation targets.

The policy adjustment comes after months of debate among economists about the appropriate balance between controlling inflation and supporting job growth. The new framework represents the most substantial change to Fed policy guidance in over a decade.

"We're recognizing that maximum employment and price stability are not competing goals but complementary objectives," the Fed Chair stated in a press conference following the announcement.

Markets reacted positively to the news, with major indices posting gains as investors interpreted the shift as supportive of continued economic growth.

However, some economists have expressed concern that the new approach could lead to higher inflation if the Fed delays rate increases to prioritize employment gains.`,
    category: 'business',
    imageUrl: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=800&fit=crop',
    imageAlt: 'Federal Reserve building exterior',
    publishedAt: '2025-01-13T20:00:00Z',
    updatedAt: '2025-01-13T22:15:00Z',
    readTime: 4,
    sources: [
      {
        source: sources[1], // WSJ
        url: 'https://wsj.com/articles/fed-policy-shift',
        title: 'Fed\'s New Framework Marks Departure from Inflation-First Approach',
        publishedAt: '2025-01-13T19:30:00Z',
        excerpt: 'The shift could mean rates stay lower for longer, boosting growth but risking price pressures...',
      },
      {
        source: sources[3], // Reuters
        url: 'https://reuters.com/markets/fed-announcement',
        title: 'Federal Reserve announces new monetary policy framework',
        publishedAt: '2025-01-13T19:00:00Z',
        excerpt: 'The central bank will now weigh employment equally with inflation in rate decisions...',
      },
      {
        source: sources[6], // Fox
        url: 'https://foxnews.com/business/fed-policy-change',
        title: 'Fed\'s policy shift raises inflation concerns among economists',
        publishedAt: '2025-01-13T20:30:00Z',
        excerpt: 'Critics warn the new approach could lead to runaway prices...',
      },
    ],
    biasDistribution: {
      left: 5,
      leanLeft: 20,
      center: 30,
      leanRight: 30,
      right: 15,
    },
    tags: ['economy', 'federal reserve', 'interest rates', 'policy'],
    isFeatured: false,
  },
  {
    id: '4',
    slug: 'quantum-computing-milestone',
    headline: 'Quantum Computer Solves Problem Beyond Classical Capabilities',
    summary: 'Tech giant announces quantum supremacy milestone, completing calculation in minutes that would take traditional supercomputers thousands of years.',
    content: `A major technology company has achieved a significant quantum computing milestone, successfully completing a complex calculation that demonstrates clear advantages over classical computing systems.

The quantum processor, utilizing 1,200 qubits, solved a optimization problem in 3.2 minutes that researchers estimate would require the world's most powerful supercomputer approximately 47,000 years to complete using traditional methods.

"This marks the transition from quantum computing as a theoretical possibility to a practical reality," said the project's lead scientist. "We're now entering an era where quantum advantages can be applied to real-world problems."

Potential applications include:
- Drug discovery and molecular simulation
- Financial modeling and risk analysis
- Cryptography and security
- Climate modeling
- Logistics optimization

The announcement has intensified the global race for quantum supremacy, with governments and corporations increasing investments in quantum research.`,
    category: 'technology',
    imageUrl: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1200&h=800&fit=crop',
    imageAlt: 'Quantum computer processor close-up',
    publishedAt: '2025-01-12T12:00:00Z',
    updatedAt: '2025-01-12T16:45:00Z',
    readTime: 5,
    sources: [
      {
        source: sources[4], // AP
        url: 'https://apnews.com/article/quantum-computing-breakthrough',
        title: 'Quantum computer achieves calculation milestone',
        publishedAt: '2025-01-12T11:00:00Z',
        excerpt: 'The achievement marks a new chapter in computing history...',
      },
      {
        source: sources[0], // NYT
        url: 'https://nytimes.com/2025/01/12/technology/quantum-supremacy.html',
        title: 'The Quantum Leap: What the Latest Breakthrough Means',
        publishedAt: '2025-01-12T12:30:00Z',
        excerpt: 'Scientists and industry leaders react to the quantum computing milestone...',
      },
      {
        source: sources[7], // Economist
        url: 'https://economist.com/technology/quantum-computing-race',
        title: 'The quantum race heats up as milestones multiply',
        publishedAt: '2025-01-12T14:00:00Z',
        excerpt: 'National security and economic implications drive government investments...',
      },
    ],
    biasDistribution: {
      left: 8,
      leanLeft: 22,
      center: 45,
      leanRight: 18,
      right: 7,
    },
    tags: ['quantum computing', 'technology', 'science', 'innovation'],
    isFeatured: true,
  },
  {
    id: '5',
    slug: 'international-trade-agreement-asia-pacific',
    headline: 'Asia-Pacific Nations Finalize Comprehensive Trade Pact',
    summary: 'Fifteen countries sign agreement eliminating tariffs on 92% of goods, creating the world\'s largest free trade zone.',
    content: `Representatives from fifteen Asia-Pacific nations have signed a comprehensive trade agreement that will eliminate tariffs on 92% of goods traded within the bloc, creating the world's largest free trade zone by GDP.

The pact, which took seven years to negotiate, covers nations representing 30% of global economic output and 2.3 billion people. It includes provisions for digital trade, intellectual property protection, and labor standards.

"This agreement positions our region for the economic challenges and opportunities of the coming decades," said the lead negotiator. "It's about ensuring prosperity for future generations."

Key provisions include:
- Elimination of 92% of tariffs within 10 years
- Standardized rules of origin
- Digital trade frameworks
- Investment protections
- Dispute resolution mechanisms

The agreement is expected to boost regional GDP by $186 billion annually once fully implemented.`,
    category: 'world',
    imageUrl: 'https://images.unsplash.com/photo-1524522173746-f628baad3644?w=1200&h=800&fit=crop',
    imageAlt: 'International trade port with cargo ships',
    publishedAt: '2025-01-11T08:00:00Z',
    updatedAt: '2025-01-11T12:30:00Z',
    readTime: 4,
    sources: [
      {
        source: sources[3], // Reuters
        url: 'https://reuters.com/world/asia-pacific-trade-deal',
        title: 'Asia-Pacific trade pact signed, world\'s largest free trade zone created',
        publishedAt: '2025-01-11T07:00:00Z',
        excerpt: 'The agreement caps years of negotiations among 15 nations...',
      },
      {
        source: sources[2], // BBC
        url: 'https://bbc.com/news/business-trade-agreement',
        title: 'Historic trade deal reshapes Asia-Pacific commerce',
        publishedAt: '2025-01-11T08:30:00Z',
        excerpt: 'The pact will affect billions of consumers and reshape supply chains...',
      },
    ],
    biasDistribution: {
      left: 12,
      leanLeft: 23,
      center: 40,
      leanRight: 18,
      right: 7,
    },
    tags: ['trade', 'international', 'economy', 'asia-pacific'],
    isFeatured: false,
  },
  {
    id: '6',
    slug: 'space-exploration-mars-mission-update',
    headline: 'Mars Mission Discovers Evidence of Ancient Microbial Life',
    summary: 'NASA\'s latest rover finds organic compounds and geological formations consistent with ancient microbial activity, potentially answering humanity\'s oldest question.',
    content: `NASA scientists announced the discovery of compelling evidence suggesting ancient microbial life once existed on Mars, marking what could be one of the most significant scientific findings in human history.

The Perseverance rover identified complex organic molecules and distinctive geological formations in Jezero Crater that researchers say are consistent with ancient microbial activity dating back approximately 3.5 billion years.

"While we need to be cautious about definitive claims, this is the strongest evidence yet that Mars once harbored life," said NASA's chief scientist. "We're looking at what appear to be biosignatures preserved in ancient sedimentary rocks."

The evidence includes:
- Complex organic molecules not easily explained by geological processes
- Stromatolite-like structures similar to those created by bacteria on Earth
- Chemical signatures consistent with metabolic processes
- Preserved environments that could have supported microbial life

Samples are being collected for eventual return to Earth for more detailed analysis.`,
    category: 'science',
    imageUrl: 'https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=1200&h=800&fit=crop',
    imageAlt: 'Mars surface with rover tracks',
    publishedAt: '2025-01-10T18:00:00Z',
    updatedAt: '2025-01-10T21:00:00Z',
    readTime: 5,
    sources: [
      {
        source: sources[4], // AP
        url: 'https://apnews.com/article/mars-life-discovery',
        title: 'NASA announces potential evidence of ancient Mars life',
        publishedAt: '2025-01-10T17:00:00Z',
        excerpt: 'Scientists urge caution while celebrating the breakthrough findings...',
      },
      {
        source: sources[0], // NYT
        url: 'https://nytimes.com/2025/01/10/science/mars-life-discovery.html',
        title: 'Are We Alone? Mars Discovery Reignites Ancient Question',
        publishedAt: '2025-01-10T18:30:00Z',
        excerpt: 'The findings could reshape our understanding of life in the universe...',
      },
      {
        source: sources[5], // Guardian
        url: 'https://theguardian.com/science/mars-microbial-life',
        title: 'Mars life evidence: What scientists found and what it means',
        publishedAt: '2025-01-10T19:00:00Z',
        excerpt: 'A detailed look at the evidence and the scientific process ahead...',
      },
    ],
    biasDistribution: {
      left: 15,
      leanLeft: 25,
      center: 45,
      leanRight: 12,
      right: 3,
    },
    tags: ['space', 'mars', 'nasa', 'science', 'discovery'],
    isFeatured: true,
  },
  {
    id: '7',
    slug: 'electric-vehicle-sales-record',
    headline: 'Electric Vehicle Sales Surge Past 50% Market Share in Europe',
    summary: 'European auto market reaches historic milestone as EVs outsell traditional combustion vehicles for the first time in monthly figures.',
    content: `Electric vehicles have crossed a significant threshold in Europe, accounting for more than half of all new car sales for the first time in history. The milestone reflects accelerating consumer adoption and expanding charging infrastructure across the continent.`,
    category: 'technology',
    imageUrl: 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=1200&h=800&fit=crop',
    imageAlt: 'Electric vehicle charging station',
    publishedAt: '2025-01-09T10:00:00Z',
    updatedAt: '2025-01-09T14:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[3], url: 'https://reuters.com/ev-sales', title: 'EV sales hit record in Europe', publishedAt: '2025-01-09T09:00:00Z', excerpt: 'The shift marks a turning point for the automotive industry...' },
      { source: sources[2], url: 'https://bbc.com/business/ev-milestone', title: 'Electric cars outsell petrol and diesel combined', publishedAt: '2025-01-09T10:30:00Z', excerpt: 'Industry analysts say the trend is accelerating faster than predicted...' },
    ],
    biasDistribution: { left: 12, leanLeft: 28, center: 40, leanRight: 15, right: 5 },
    tags: ['electric vehicles', 'automotive', 'climate', 'europe'],
    isFeatured: false,
  },
  {
    id: '8',
    slug: 'cybersecurity-breach-financial-sector',
    headline: 'Major Banks Respond to Coordinated Cyber Attack on Financial Systems',
    summary: 'Multiple financial institutions report sophisticated hacking attempts targeting international payment networks, prompting emergency security measures.',
    content: `Several major international banks have disclosed coordinated cyber attacks targeting their payment processing systems. Security experts describe the incident as one of the most sophisticated attacks on financial infrastructure in recent years.`,
    category: 'business',
    imageUrl: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1200&h=800&fit=crop',
    imageAlt: 'Cybersecurity operations center',
    publishedAt: '2025-01-08T16:00:00Z',
    updatedAt: '2025-01-08T20:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[1], url: 'https://wsj.com/cyber-attack-banks', title: 'Banks Face Unprecedented Cyber Threat', publishedAt: '2025-01-08T15:00:00Z', excerpt: 'The coordinated attack targeted payment processing systems...' },
      { source: sources[3], url: 'https://reuters.com/finance/cyber-breach', title: 'Financial sector on high alert after cyber attack', publishedAt: '2025-01-08T16:30:00Z', excerpt: 'Regulators are working with banks to assess the damage...' },
    ],
    biasDistribution: { left: 8, leanLeft: 22, center: 45, leanRight: 18, right: 7 },
    tags: ['cybersecurity', 'banking', 'finance', 'technology'],
    isFeatured: false,
  },
  {
    id: '9',
    slug: 'renewable-energy-investment-record',
    headline: 'Global Renewable Energy Investment Hits $1.8 Trillion in 2024',
    summary: 'Clean energy investments reach historic high as solar and wind costs continue to fall, surpassing fossil fuel investments for the third consecutive year.',
    content: `Global investment in renewable energy sources reached an unprecedented $1.8 trillion in 2024, marking a 25% increase from the previous year and cementing the clean energy transition as an economic reality.`,
    category: 'environment',
    imageUrl: 'https://images.unsplash.com/photo-1509391366360-2e959784a276?w=1200&h=800&fit=crop',
    imageAlt: 'Solar panel farm at sunset',
    publishedAt: '2025-01-07T12:00:00Z',
    updatedAt: '2025-01-07T15:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[7], url: 'https://economist.com/energy-investment', title: 'The green energy boom accelerates', publishedAt: '2025-01-07T11:00:00Z', excerpt: 'Investment figures show accelerating transition away from fossil fuels...' },
      { source: sources[5], url: 'https://theguardian.com/environment/renewables', title: 'Renewable energy investment hits record high', publishedAt: '2025-01-07T12:30:00Z', excerpt: 'Solar and wind lead the charge as costs continue to plummet...' },
    ],
    biasDistribution: { left: 20, leanLeft: 30, center: 35, leanRight: 12, right: 3 },
    tags: ['renewable energy', 'investment', 'climate', 'solar', 'wind'],
    isFeatured: false,
  },
  {
    id: '10',
    slug: 'ai-regulation-european-union',
    headline: 'EU Passes Comprehensive AI Regulation Framework',
    summary: 'European Parliament approves landmark artificial intelligence rules establishing risk-based approach and transparency requirements for AI systems.',
    content: `The European Union has adopted the world's most comprehensive framework for regulating artificial intelligence, establishing strict requirements for high-risk AI applications and banning certain uses altogether.`,
    category: 'politics',
    imageUrl: 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1200&h=800&fit=crop',
    imageAlt: 'European Parliament building',
    publishedAt: '2025-01-06T14:00:00Z',
    updatedAt: '2025-01-06T18:00:00Z',
    readTime: 6,
    sources: [
      { source: sources[2], url: 'https://bbc.com/eu-ai-rules', title: 'EU agrees landmark AI rules', publishedAt: '2025-01-06T13:00:00Z', excerpt: 'The regulation will affect tech companies worldwide...' },
      { source: sources[0], url: 'https://nytimes.com/eu-ai-regulation', title: 'Europe Takes Lead in AI Governance', publishedAt: '2025-01-06T14:30:00Z', excerpt: 'The framework could become a global model for AI oversight...' },
    ],
    biasDistribution: { left: 18, leanLeft: 27, center: 35, leanRight: 15, right: 5 },
    tags: ['AI', 'regulation', 'european union', 'technology', 'policy'],
    isFeatured: false,
  },
  {
    id: '11',
    slug: 'housing-market-trends-2025',
    headline: 'Housing Market Shows Signs of Stabilization After Rate Adjustments',
    summary: 'Real estate analysts report moderating prices and increasing inventory as mortgage rates begin to ease from recent highs.',
    content: `The housing market is showing signs of returning to balance after two years of volatility, with prices stabilizing in major metropolitan areas and inventory levels rising to pre-pandemic levels.`,
    category: 'business',
    imageUrl: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1200&h=800&fit=crop',
    imageAlt: 'Suburban houses aerial view',
    publishedAt: '2025-01-05T09:00:00Z',
    updatedAt: '2025-01-05T12:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[1], url: 'https://wsj.com/housing-market', title: 'Housing Market Finds Footing', publishedAt: '2025-01-05T08:00:00Z', excerpt: 'Lower mortgage rates are bringing buyers back to the market...' },
      { source: sources[3], url: 'https://reuters.com/property/housing-trends', title: 'US housing market stabilizes', publishedAt: '2025-01-05T09:30:00Z', excerpt: 'Inventory increases provide relief for buyers...' },
    ],
    biasDistribution: { left: 10, leanLeft: 20, center: 40, leanRight: 22, right: 8 },
    tags: ['housing', 'real estate', 'economy', 'mortgages'],
    isFeatured: false,
  },
  {
    id: '12',
    slug: 'gene-therapy-breakthrough-rare-diseases',
    headline: 'Gene Therapy Cures Previously Untreatable Genetic Disorder',
    summary: 'FDA approves revolutionary gene therapy that has successfully treated patients with a rare genetic condition, offering hope for similar applications.',
    content: `A groundbreaking gene therapy has received FDA approval after demonstrating complete remission in patients suffering from a previously incurable genetic disorder, marking a new era in precision medicine.`,
    category: 'health',
    imageUrl: 'https://images.unsplash.com/photo-1579154204601-01588f351e67?w=1200&h=800&fit=crop',
    imageAlt: 'Gene therapy laboratory',
    publishedAt: '2025-01-04T11:00:00Z',
    updatedAt: '2025-01-04T15:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[4], url: 'https://apnews.com/gene-therapy-approval', title: 'FDA approves landmark gene therapy', publishedAt: '2025-01-04T10:00:00Z', excerpt: 'The treatment offers hope to thousands of patients worldwide...' },
      { source: sources[0], url: 'https://nytimes.com/health/gene-therapy', title: 'A Cure Long Sought: Gene Therapy Transforms Lives', publishedAt: '2025-01-04T11:30:00Z', excerpt: 'Patients describe the treatment as life-changing...' },
    ],
    biasDistribution: { left: 12, leanLeft: 25, center: 45, leanRight: 13, right: 5 },
    tags: ['gene therapy', 'healthcare', 'FDA', 'medicine', 'genetics'],
    isFeatured: false,
  },
  {
    id: '13',
    slug: 'global-food-security-summit',
    headline: 'World Leaders Address Growing Food Security Concerns at UN Summit',
    summary: 'Nations commit to new initiatives addressing hunger and agricultural sustainability as climate change threatens global food production.',
    content: `World leaders gathered at the United Nations to address escalating food security challenges, pledging coordinated action to combat hunger and develop climate-resilient agricultural practices.`,
    category: 'world',
    imageUrl: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=1200&h=800&fit=crop',
    imageAlt: 'UN General Assembly hall',
    publishedAt: '2025-01-03T16:00:00Z',
    updatedAt: '2025-01-03T20:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[3], url: 'https://reuters.com/un-food-summit', title: 'UN summit tackles global hunger crisis', publishedAt: '2025-01-03T15:00:00Z', excerpt: 'Leaders announce new funding commitments for food security...' },
      { source: sources[5], url: 'https://theguardian.com/food-security', title: 'Climate change driving food crisis, summit hears', publishedAt: '2025-01-03T16:30:00Z', excerpt: 'Agricultural experts warn of worsening conditions without action...' },
    ],
    biasDistribution: { left: 22, leanLeft: 28, center: 32, leanRight: 13, right: 5 },
    tags: ['food security', 'UN', 'climate', 'hunger', 'international'],
    isFeatured: false,
  },
  {
    id: '14',
    slug: 'smartphone-industry-innovation-2025',
    headline: 'Major Tech Companies Unveil Next Generation Smartphone Features',
    summary: 'Annual consumer electronics show showcases revolutionary smartphone capabilities including advanced AI integration and satellite connectivity.',
    content: `The world's leading smartphone manufacturers unveiled their latest innovations at this year's consumer electronics show, featuring AI-powered assistants, improved satellite connectivity, and revolutionary camera systems.`,
    category: 'technology',
    imageUrl: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=1200&h=800&fit=crop',
    imageAlt: 'Modern smartphones display',
    publishedAt: '2025-01-02T10:00:00Z',
    updatedAt: '2025-01-02T14:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[7], url: 'https://economist.com/tech-ces', title: 'The future of mobile technology', publishedAt: '2025-01-02T09:00:00Z', excerpt: 'New features promise to transform how we use our devices...' },
      { source: sources[2], url: 'https://bbc.com/tech/smartphones-2025', title: 'Smartphone innovations steal the show at CES', publishedAt: '2025-01-02T10:30:00Z', excerpt: 'AI integration leads the way in new device announcements...' },
    ],
    biasDistribution: { left: 8, leanLeft: 22, center: 48, leanRight: 17, right: 5 },
    tags: ['smartphones', 'technology', 'CES', 'AI', 'mobile'],
    isFeatured: false,
  },
  {
    id: '15',
    slug: 'ocean-conservation-breakthrough',
    headline: 'Scientists Report Recovery of Critical Marine Ecosystems',
    summary: 'Marine protected areas show significant ecosystem recovery, with coral reefs and fish populations rebounding faster than expected.',
    content: `A comprehensive study of marine protected areas has revealed encouraging signs of ecosystem recovery, with coral reef coverage and fish populations increasing significantly in zones where fishing and development have been restricted.`,
    category: 'science',
    imageUrl: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=1200&h=800&fit=crop',
    imageAlt: 'Coral reef underwater',
    publishedAt: '2025-01-01T12:00:00Z',
    updatedAt: '2025-01-01T16:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[5], url: 'https://theguardian.com/ocean-recovery', title: 'Marine life rebounds in protected waters', publishedAt: '2025-01-01T11:00:00Z', excerpt: 'The findings offer hope for ocean conservation efforts worldwide...' },
      { source: sources[4], url: 'https://apnews.com/ocean-ecosystems', title: 'Ocean ecosystems showing signs of recovery', publishedAt: '2025-01-01T12:30:00Z', excerpt: 'Scientists credit marine protected areas for the improvement...' },
    ],
    biasDistribution: { left: 18, leanLeft: 30, center: 38, leanRight: 10, right: 4 },
    tags: ['ocean', 'conservation', 'marine life', 'environment', 'science'],
    isFeatured: false,
  },
  {
    id: '16',
    slug: 'education-technology-transformation',
    headline: 'Schools Embrace AI-Powered Personalized Learning Systems',
    summary: 'Education districts across the country adopt adaptive learning platforms that customize curriculum to individual student needs.',
    content: `A growing number of school districts are implementing AI-powered adaptive learning systems that personalize educational content based on individual student performance, learning style, and pace.`,
    category: 'technology',
    imageUrl: 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1200&h=800&fit=crop',
    imageAlt: 'Students using tablets in classroom',
    publishedAt: '2024-12-31T14:00:00Z',
    updatedAt: '2024-12-31T18:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[0], url: 'https://nytimes.com/education/ai-learning', title: 'AI Transforms the Classroom', publishedAt: '2024-12-31T13:00:00Z', excerpt: 'Personalized learning shows promise in early adopter schools...' },
      { source: sources[2], url: 'https://bbc.com/education/ai-schools', title: 'How AI is changing education', publishedAt: '2024-12-31T14:30:00Z', excerpt: 'Teachers report improved student engagement with new tools...' },
    ],
    biasDistribution: { left: 14, leanLeft: 26, center: 40, leanRight: 15, right: 5 },
    tags: ['education', 'AI', 'technology', 'schools', 'learning'],
    isFeatured: false,
  },
  {
    id: '17',
    slug: 'infrastructure-bill-implementation',
    headline: 'Major Infrastructure Projects Begin Across the Nation',
    summary: 'Construction starts on bridges, highways, and broadband networks as funding from landmark infrastructure legislation begins flowing.',
    content: `Construction crews have broken ground on dozens of major infrastructure projects across the country, marking the beginning of the largest public works initiative in decades funded by recent federal legislation.`,
    category: 'politics',
    imageUrl: 'https://images.unsplash.com/photo-1590496793929-36417d3117de?w=1200&h=800&fit=crop',
    imageAlt: 'Bridge construction site',
    publishedAt: '2024-12-30T11:00:00Z',
    updatedAt: '2024-12-30T15:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[4], url: 'https://apnews.com/infrastructure-projects', title: 'Infrastructure spending ramps up nationwide', publishedAt: '2024-12-30T10:00:00Z', excerpt: 'Thousands of jobs expected as construction begins...' },
      { source: sources[1], url: 'https://wsj.com/infrastructure-impact', title: 'Infrastructure Bill: What Gets Built and Where', publishedAt: '2024-12-30T11:30:00Z', excerpt: 'Analysis of where federal dollars will have the biggest impact...' },
    ],
    biasDistribution: { left: 16, leanLeft: 24, center: 35, leanRight: 18, right: 7 },
    tags: ['infrastructure', 'politics', 'construction', 'economy', 'federal'],
    isFeatured: false,
  },
  {
    id: '18',
    slug: 'mental-health-workplace-initiatives',
    headline: 'Companies Expand Mental Health Benefits Amid Growing Demand',
    summary: 'Major employers introduce comprehensive mental health programs as workers increasingly prioritize wellbeing in job decisions.',
    content: `Leading corporations are significantly expanding their mental health benefits, responding to employee demand and research showing the productivity benefits of supporting worker wellbeing.`,
    category: 'health',
    imageUrl: 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=1200&h=800&fit=crop',
    imageAlt: 'Modern office wellness space',
    publishedAt: '2024-12-29T09:00:00Z',
    updatedAt: '2024-12-29T13:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[1], url: 'https://wsj.com/workplace-mental-health', title: 'Companies Bet Big on Mental Health Benefits', publishedAt: '2024-12-29T08:00:00Z', excerpt: 'ROI studies show productivity gains from wellness investments...' },
      { source: sources[5], url: 'https://theguardian.com/mental-health-work', title: 'The workplace mental health revolution', publishedAt: '2024-12-29T09:30:00Z', excerpt: 'Workers increasingly expect mental health support from employers...' },
    ],
    biasDistribution: { left: 20, leanLeft: 28, center: 34, leanRight: 13, right: 5 },
    tags: ['mental health', 'workplace', 'benefits', 'wellness', 'business'],
    isFeatured: false,
  },
  {
    id: '19',
    slug: 'autonomous-vehicles-expansion',
    headline: 'Self-Driving Taxi Services Expand to Major Metropolitan Areas',
    summary: 'Autonomous vehicle companies receive approval to operate in additional cities, marking significant expansion of driverless transportation.',
    content: `Several autonomous vehicle companies have received regulatory approval to expand their self-driving taxi services to major metropolitan areas, bringing driverless transportation to millions of new potential users.`,
    category: 'technology',
    imageUrl: 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=1200&h=800&fit=crop',
    imageAlt: 'Autonomous vehicle on city street',
    publishedAt: '2024-12-28T15:00:00Z',
    updatedAt: '2024-12-28T19:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[3], url: 'https://reuters.com/autonomous-expansion', title: 'Self-driving taxis coming to more cities', publishedAt: '2024-12-28T14:00:00Z', excerpt: 'Regulatory approvals pave the way for service expansion...' },
      { source: sources[7], url: 'https://economist.com/autonomous-future', title: 'The autonomous vehicle market heats up', publishedAt: '2024-12-28T15:30:00Z', excerpt: 'Competition intensifies as companies race to expand coverage...' },
    ],
    biasDistribution: { left: 10, leanLeft: 24, center: 44, leanRight: 17, right: 5 },
    tags: ['autonomous vehicles', 'transportation', 'technology', 'urban', 'mobility'],
    isFeatured: false,
  },
  {
    id: '20',
    slug: 'cultural-heritage-digital-preservation',
    headline: 'Museums Launch Global Digital Archive of Cultural Artifacts',
    summary: 'Major institutions collaborate to create comprehensive online database preserving cultural heritage using 3D scanning and virtual reality.',
    content: `The world's leading museums have joined forces to create a comprehensive digital archive of cultural artifacts, using advanced 3D scanning and virtual reality technology to preserve and share humanity's cultural heritage.`,
    category: 'culture',
    imageUrl: 'https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1200&h=800&fit=crop',
    imageAlt: 'Museum exhibition hall',
    publishedAt: '2024-12-27T12:00:00Z',
    updatedAt: '2024-12-27T16:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[2], url: 'https://bbc.com/culture/digital-museums', title: 'Museums go digital to preserve history', publishedAt: '2024-12-27T11:00:00Z', excerpt: 'Virtual tours bring artifacts to global audiences...' },
      { source: sources[0], url: 'https://nytimes.com/arts/digital-archive', title: 'The Museum Without Walls Goes Online', publishedAt: '2024-12-27T12:30:00Z', excerpt: 'Technology opens new possibilities for cultural preservation...' },
    ],
    biasDistribution: { left: 15, leanLeft: 25, center: 42, leanRight: 14, right: 4 },
    tags: ['culture', 'museums', 'digital', 'preservation', 'technology'],
    isFeatured: false,
  },
  {
    id: '21',
    slug: 'supply-chain-resilience-strategies',
    headline: 'Companies Invest Billions in Supply Chain Diversification',
    summary: 'Global businesses accelerate efforts to build more resilient supply networks following recent disruptions and geopolitical tensions.',
    content: `Major corporations are investing heavily in supply chain diversification and nearshoring strategies, seeking to build more resilient networks capable of withstanding disruptions and geopolitical uncertainties.`,
    category: 'business',
    imageUrl: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1200&h=800&fit=crop',
    imageAlt: 'Logistics warehouse interior',
    publishedAt: '2024-12-26T10:00:00Z',
    updatedAt: '2024-12-26T14:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[1], url: 'https://wsj.com/supply-chain-investment', title: 'Supply Chain Overhaul Accelerates', publishedAt: '2024-12-26T09:00:00Z', excerpt: 'Companies prioritize resilience over efficiency...' },
      { source: sources[7], url: 'https://economist.com/logistics-transformation', title: 'The great supply chain restructuring', publishedAt: '2024-12-26T10:30:00Z', excerpt: 'Geopolitical risks drive strategic manufacturing shifts...' },
    ],
    biasDistribution: { left: 8, leanLeft: 20, center: 42, leanRight: 23, right: 7 },
    tags: ['supply chain', 'business', 'logistics', 'manufacturing', 'global trade'],
    isFeatured: false,
  },
  {
    id: '22',
    slug: 'youth-climate-activism-impact',
    headline: 'Young Climate Activists Credited with Shifting Policy Debate',
    summary: 'Analysis shows growing influence of youth-led movements on environmental policy decisions at local and national levels.',
    content: `A new analysis reveals the significant impact youth climate activists have had on environmental policy, with their advocacy credited for shifting public opinion and influencing legislative priorities across multiple countries.`,
    category: 'environment',
    imageUrl: 'https://images.unsplash.com/photo-1591848478625-de43268e6fb8?w=1200&h=800&fit=crop',
    imageAlt: 'Youth climate protest',
    publishedAt: '2024-12-25T14:00:00Z',
    updatedAt: '2024-12-25T18:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[5], url: 'https://theguardian.com/youth-climate', title: 'How young activists changed the climate debate', publishedAt: '2024-12-25T13:00:00Z', excerpt: 'Youth movements have reshaped environmental politics...' },
      { source: sources[2], url: 'https://bbc.com/environment/youth-activism', title: 'The rise of young climate leaders', publishedAt: '2024-12-25T14:30:00Z', excerpt: 'New generation of activists drives policy change...' },
    ],
    biasDistribution: { left: 28, leanLeft: 32, center: 25, leanRight: 10, right: 5 },
    tags: ['climate', 'activism', 'youth', 'environment', 'policy'],
    isFeatured: false,
  },
  {
    id: '23',
    slug: 'international-space-station-future',
    headline: 'Space Agencies Outline Plans for Next-Generation Orbital Station',
    summary: 'International consortium announces collaborative effort to develop successor to aging International Space Station.',
    content: `Space agencies from multiple nations have unveiled plans for a next-generation orbital research station, designed to replace the aging International Space Station and expand humanity's presence in low Earth orbit.`,
    category: 'science',
    imageUrl: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1200&h=800&fit=crop',
    imageAlt: 'International Space Station in orbit',
    publishedAt: '2024-12-24T16:00:00Z',
    updatedAt: '2024-12-24T20:00:00Z',
    readTime: 5,
    sources: [
      { source: sources[4], url: 'https://apnews.com/space-station-future', title: 'New space station plans unveiled', publishedAt: '2024-12-24T15:00:00Z', excerpt: 'International collaboration will shape humanity\'s orbital future...' },
      { source: sources[3], url: 'https://reuters.com/space/station-successor', title: 'Space agencies plan ISS replacement', publishedAt: '2024-12-24T16:30:00Z', excerpt: 'The new station will feature expanded research capabilities...' },
    ],
    biasDistribution: { left: 10, leanLeft: 22, center: 48, leanRight: 15, right: 5 },
    tags: ['space', 'ISS', 'NASA', 'international', 'science'],
    isFeatured: false,
  },
  {
    id: '24',
    slug: 'digital-currency-adoption-accelerates',
    headline: 'Central Banks Accelerate Digital Currency Development',
    summary: 'Multiple countries announce progress on central bank digital currencies as the global financial system evolves.',
    content: `Central banks worldwide are accelerating their development of digital currencies, with several nations moving toward pilot programs and eventual public launch of government-backed digital money.`,
    category: 'business',
    imageUrl: 'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=1200&h=800&fit=crop',
    imageAlt: 'Digital currency concept',
    publishedAt: '2024-12-23T11:00:00Z',
    updatedAt: '2024-12-23T15:00:00Z',
    readTime: 4,
    sources: [
      { source: sources[1], url: 'https://wsj.com/digital-currency-cbdc', title: 'Central Banks Race to Launch Digital Currencies', publishedAt: '2024-12-23T10:00:00Z', excerpt: 'CBDCs could transform global finance within the decade...' },
      { source: sources[7], url: 'https://economist.com/finance/digital-money', title: 'The future of money goes digital', publishedAt: '2024-12-23T11:30:00Z', excerpt: 'Governments seek to maintain monetary control in digital age...' },
    ],
    biasDistribution: { left: 10, leanLeft: 22, center: 40, leanRight: 20, right: 8 },
    tags: ['digital currency', 'central banks', 'finance', 'technology', 'CBDC'],
    isFeatured: false,
  },
]

export function getArticleBySlug(slug: string): Article | undefined {
  return mockArticles.find((article) => article.slug === slug)
}

export function getArticlesByCategory(category: string): Article[] {
  return mockArticles.filter((article) => article.category === category)
}

export function getFeaturedArticles(): Article[] {
  return mockArticles.filter((article) => article.isFeatured)
}

export function getBreakingNews(): Article[] {
  return mockArticles.filter((article) => article.isBreaking)
}

export function getSourceById(id: string): Source | undefined {
  return sources.find((source) => source.id === id)
}

export function getBiasLabel(bias: string): string {
  const labels: Record<string, string> = {
    left: 'Left',
    'lean-left': 'Lean Left',
    center: 'Center',
    'lean-right': 'Lean Right',
    right: 'Right',
  }
  return labels[bias] || bias
}

export function getBiasColor(bias: string): string {
  const colors: Record<string, string> = {
    left: 'var(--color-bias-left)',
    'lean-left': 'color-mix(in oklch, var(--color-bias-left), var(--color-bias-center))',
    center: 'var(--color-bias-center)',
    'lean-right': 'color-mix(in oklch, var(--color-bias-right), var(--color-bias-center))',
    right: 'var(--color-bias-right)',
  }
  return colors[bias] || 'var(--color-text-tertiary)'
}
