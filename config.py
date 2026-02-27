"""
Central configuration: RSS feeds, defaults, and constants.
"""

# Predefined RSS feeds for German-language business/economy news
RSS_FEEDS = [
    {
        "name": "NZZ Wirtschaft",
        "url": "https://www.nzz.ch/wirtschaft.rss",
    },
    {
        "name": "SRF Wirtschaft",
        "url": "https://www.srf.ch/news/bnf/rss/1926",
    },
    {
        "name": "Tages-Anzeiger Wirtschaft",
        "url": "https://partner-feeds.publishing.tamedia.ch/rss/tagesanzeiger/wirtschaft",
    },
    {
        "name": "Google News Wirtschaft CH",
        "url": "https://news.google.com/rss/search?q=wirtschaft+schweiz&hl=de&gl=CH&ceid=CH:de",
    },
]

# How many days back to fetch data from GA4 and GSC
ANALYTICS_DAYS_BACK = 7

# Longer lookback period for evergreen/trend comparison
ANALYTICS_DAYS_LONG = 90

# How many top GA4 pages to crawl for existing-content analysis
CRAWL_TOP_PAGES = 10

# How many content ideas to generate
IDEAS_COUNT = 5

# Google Trends settings
TRENDS_GEO = "CH"          # Region für Google Trends
TRENDS_LIMIT = 20           # Anzahl trendender Keywords

TRENDS_KEYWORDS = [
    # Geldpolitik & Finanzen
    "SNB", "Inflation Schweiz", "Zinsen Schweiz", "Franken", "Hypothek",
    # Arbeitsmarkt
    "Arbeitslosigkeit Schweiz", "Mindestlohn", "Fachkräftemangel", "Lohnentwicklung",
    # Konjunktur & Unternehmen
    "Konjunktur Schweiz", "BIP Schweiz", "KMU Schweiz", "Firmengründung",
    # Soziales
    "AHV Reform", "Krankenkasse Prämien", "Rentenalter",
    # Energie
    "Strompreise Schweiz", "Energiewende Schweiz",
    # Handel & EU
    "Bilaterale Abkommen", "Freihandel Schweiz",
    # Steuern
    "Steuern Schweiz", "OECD Mindeststeuer",
    # Digital
    "KI Schweiz", "Digitalisierung Wirtschaft",
]

# Max RSS items to fetch per feed (before filtering)
RSS_MAX_ITEMS_PER_FEED = 15

# OpenAI model used by all agents
OPENAI_MODEL = "gpt-5.2"
OPENAI_MODEL_PRO = OPENAI_MODEL

# --- Content creation settings ---

# Target word count for generated articles
ARTICLE_TARGET_WORDS = 1200

# Maximum number of Writer revision loops (after initial draft)
MAX_REVISION_LOOPS = 2

# Minimum evaluator score (0-100) to accept an article
EVALUATOR_MIN_SCORE = 80

BRAND_VOICE = """
Sachlich, direkt und faktenbasiert. Komplexe Wirtschaftsthemen
verständlich und ohne Jargon erklären. Schweizer Perspektive
wo relevant. Keine werbliche Sprache, kein Eigenlob.
"""

FORBIDDEN_PHRASES = [
    "In der heutigen schnelllebigen Welt",
    "bahnbrechend",
    "revolutionär",
    "optimieren",
    "nachhaltiger Mehrwert",
    "ganzheitlich",
    "synergetisch",
    "proaktiv",
    "es gilt",
    "nicht zuletzt",
]
