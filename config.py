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
]

# How many days back to fetch data from GA4 and GSC
ANALYTICS_DAYS_BACK = 7

# How many content ideas to generate
IDEAS_COUNT = 10

# Max RSS items to fetch per feed (before filtering)
RSS_MAX_ITEMS_PER_FEED = 15

# OpenAI model for idea-generation agents (analyst, trend scout, strategist, editor)
OPENAI_MODEL = "gpt-5.2"

# OpenAI model for article-writing agents (researcher, writer, fact checker, evaluator)
OPENAI_MODEL_PRO = "gpt-5.2-pro"

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
