# Technische Dokumentation – Content-Ideen-Generator

*Dokumentation für Entwickler, IT-Entscheider und CTOs*

---

## 1. Architektur-Übersicht

### Stack

| Komponente | Technologie |
|------------|-------------|
| Laufzeit | Python 3.12 |
| Web-Framework | Streamlit (Single-Page-App) |
| KI-Modell | OpenAI GPT-5.2 (`gpt-5.2`) via OpenAI Python SDK |
| Analytics | Google Analytics Data API v1 Beta |
| Search | Google Search Console API v3 (webmasters) |
| Authentifizierung (Google) | Service Account (JSON-Key) |
| RSS-Parsing | feedparser |
| Web-Crawling | requests + stdlib `html.parser` |
| PDF-Export | fpdf2 (Pure-Python, keine Systemabhängigkeiten) |
| Persistenz | Lokale JSON-Datei (`data/ideas_history.json`) |
| Umgebungsvariablen | python-dotenv (`.env`-Datei oder Streamlit Secrets) |

### Deployment
Das System ist als Streamlit-App konzipiert und kann lokal (`streamlit run app.py`) oder über Streamlit Community Cloud betrieben werden. Für Streamlit Cloud werden Geheimnisse über `st.secrets` injiziert und automatisch in `os.environ` überführt.

Keine Datenbank, kein externer State-Store – alle Laufzeitdaten liegen im Streamlit Session State bzw. im lokalen Dateisystem.

---

## 2. Projektstruktur

```
content-idea-generator/
│
├── app.py                          # Streamlit UI – Einstiegspunkt
├── pipeline.py                     # Ideen-Pipeline-Orchestrator (4 Agenten)
├── content_pipeline.py             # Artikel-Pipeline-Orchestrator (5 Agenten)
├── evaluation_pipeline.py          # Bewertungs-Pipeline-Orchestrator (2 Agenten)
├── export.py                       # Artikel-Export: Markdown + PDF (fpdf2)
├── config.py                       # Zentrale Konfiguration (Konstanten, Feeds)
│
├── agents/
│   ├── analyst.py                  # Agent 1: GA4 + GSC Analyse
│   ├── trend_scout.py              # Agent 2: RSS-Feed-Analyse
│   ├── strategist.py               # Agent 3: Ideen-Konzeption
│   ├── editor.py                   # Agent 4: Ideen-Verfeinerung + JSON-Output
│   ├── researcher.py               # Agent 5: Faktenrecherche für Artikel
│   ├── writer.py                   # Agent 6: Artikel-Erstellung
│   ├── fact_checker.py             # Agent 7: Faktenprüfung
│   ├── evaluator.py                # Agent 8: Qualitätsbewertung
│   ├── social_writer.py            # Agent 9: Social-Media-Texte
│   ├── idea_context.py             # Agent 10: Kontext-Suche (Ideen-Prüfung)
│   └── idea_evaluator.py           # Agent 11: Ideen-Bewertung (Ideen-Prüfung)
│
├── data/
│   ├── google_analytics.py         # GA4 API-Client
│   ├── search_console.py           # GSC API-Client
│   ├── rss_reader.py               # RSS-Feed-Fetcher
│   ├── content_crawler.py          # Website-Crawler
│   ├── google_trends.py            # Google Trends-Client (pytrends)
│   └── ideas_history.json          # Persistierte Ideen-Runs (auto-created)
│
├── .env                            # Lokale Umgebungsvariablen (nicht committed)
├── requirements.txt                # Python-Abhängigkeiten
└── credentials.json                # Google Service Account Key (nicht committed)
```

---

## 3. Datenquellen & APIs

### 3.1 Google Analytics 4 (`data/google_analytics.py`)

**Funktion:** `fetch_top_pages(property_id, credentials_file, days_back, limit)`

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `property_id` | `str` | – | GA4-Property-ID (z.B. `"123456789"`) |
| `credentials_file` | `str` | – | Pfad zur Service-Account-JSON-Datei |
| `days_back` | `int` | `7` | Lookback-Zeitraum in Tagen |
| `limit` | `int` | `20` | Maximale Anzahl Ergebniszeilen |

**GA4-Dimensionen:** `pageTitle`, `pagePath`
**GA4-Metriken:** `screenPageViews`, `engagementRate`
**Sortierung:** `screenPageViews` absteigend

**Return-Format:** `list[dict]`
```python
[
    {
        "page_title": str,        # Seitentitel
        "page_path": str,         # URL-Pfad (z.B. "/artikel/ezb-zinsen")
        "page_views": int,        # Anzahl Seitenaufrufe
        "engagement_rate": float, # Engagement-Rate in % (0–100)
    },
    ...
]
```

**Authentifizierung:** Service Account via `google-auth` Library. Unterstützt JSON-Inhalt direkt in `GOOGLE_CREDENTIALS_JSON` (Env-Var) oder als Dateipfad in `GOOGLE_CREDENTIALS_FILE`. Eingebaute Behandlung von Newlines in Private-Key-Strings.

---

### 3.2 Google Search Console (`data/search_console.py`)

**Funktion 1:** `fetch_top_queries(site_url, credentials_file, days_back, limit)`

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `site_url` | `str` | – | GSC-Site-URL (z.B. `"https://example.com/"`) |
| `credentials_file` | `str` | – | Pfad zur Service-Account-JSON-Datei |
| `days_back` | `int` | `7` | Lookback-Zeitraum in Tagen |
| `limit` | `int` | `25` | Maximale Anzahl Ergebniszeilen |

**Dimension:** `query` | **Sortierung:** `impressions` absteigend

**Return-Format:** `list[dict]`
```python
[
    {
        "query": str,        # Suchanfrage
        "impressions": int,  # Anzahl Impressionen
        "clicks": int,       # Anzahl Klicks
        "ctr": float,        # Click-Through-Rate in % (gerundet auf 2 Stellen)
        "position": float,   # Ø Google-Position (gerundet auf 1 Stelle)
    },
    ...
]
```

---

**Funktion 2:** `fetch_top_pages_by_position(site_url, credentials_file, days_back, limit, min_position, max_position)`

Identifiziert seitenbasiert die Google-Positionen. Primär genutzt für Fast-Ranker-Erkennung (Position 4–15).

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `min_position` | `float` | `1.0` | Untergrenze Position-Filter |
| `max_position` | `float` | `20.0` | Obergrenze Position-Filter |

**Return-Format:** `list[dict]`
```python
[
    {
        "page": str,         # Vollständige URL
        "impressions": int,
        "clicks": int,
        "ctr": float,        # in %
        "position": float,   # Ø Position, aufsteigend sortiert
    },
    ...
]
```

**API-Endpunkt:** `webmasters.searchanalytics.query` (Google Search Console API v3)
**Scope:** `https://www.googleapis.com/auth/webmasters.readonly`

---

### 3.3 RSS-Feed-Fetcher (`data/rss_reader.py`)

Ruft die in `config.RSS_FEEDS` definierten Feeds ab. Pro Feed werden max. `RSS_MAX_ITEMS_PER_FEED` (Standard: 15) Artikel geladen. Es existiert eine separate Funktion `fetch_google_news_articles(query)` für dynamische Google News-Suche nach einem Suchbegriff (genutzt in der Bewertungs-Pipeline).

**Return-Format pro Artikel:** `list[dict]`
```python
{
    "title": str,       # Artikel-Titel
    "url": str,         # Artikel-URL
    "source": str,      # Quellname (z.B. "NZZ Wirtschaft")
    "published": datetime | None,  # Publikationsdatum
    "summary": str,     # Kurzzusammenfassung / Teaser
}
```

---

### 3.4 Website-Crawler (`data/content_crawler.py`)

Lightweight-Crawler auf Basis von `requests` + stdlib `html.parser`. Kein Headless-Browser, kein JavaScript-Rendering.

**Funktion:** `crawl_top_pages(ga4_pages, base_url, limit)`

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `ga4_pages` | `list[dict]` | – | GA4-Ergebnis-Liste (benötigt `page_path`) |
| `base_url` | `str` | – | Root-URL der Website |
| `limit` | `int` | `10` | Max. Anzahl zu crawlender Seiten |

**Return-Format:** `list[dict]`
```python
{
    "url": str,               # Vollständige URL
    "title": str,             # <title> oder <h1>
    "summary": str,           # Erste 4 Sätze des Textes
    "word_count": int,        # Wörteranzahl (sichtbarer Text)
    "estimated_date": str,    # Publikationsdatum (YYYY-MM-DD, best-effort)
    "error": str | None,      # Fehlermeldung bei Fehler
    "page_views": int,        # Aus GA4-Daten angereichert
    "engagement_rate": float, # Aus GA4-Daten angereichert
}
```

**Technische Details:**
- In-Memory-Cache: Jede URL wird pro Prozess-Laufzeit nur einmal gecrawlt
- Polite Crawl Delay: 0,3 Sekunden zwischen Requests
- Timeout: 8 Sekunden pro Request
- User-Agent: `Mozilla/5.0 (compatible; ContentIdeaBot/1.0; +https://github.com)`
- Datums-Extraktion: Meta-Tags (`article:published_time`, `datePublished`) + JSON-LD
- Ignorierte Tags: `script`, `style`, `nav`, `footer`, `header`, `aside`, `noscript`

**Formatierungsfunktion:** `format_crawl_summaries(crawled)` → `str`
Wandelt die crawl-Ergebnisse in einen formatierten Markdown-Textblock für Agent-Prompts um.

---

### 3.5 Google Trends (`data/google_trends.py`)

Ruft via `pytrends` trendende Suchanfragen in der Schweiz (`geo="CH"`) ab. Die Konfiguration (`TRENDS_KEYWORDS`, `TRENDS_GEO`, `TRENDS_LIMIT`) liegt in `config.py`.

**Return-Format:** `list[dict]`
```python
[
    {"keyword": str, "value": int},  # value = relativer Trend-Index 0–100
    ...
]
```

Fehler (z.B. Rate-Limit) werden silent ignoriert und geben eine leere Liste zurück.

---

### 3.6 Artikel-Export (`export.py`)

Stellt zwei öffentliche Funktionen für den Download-Export bereit.

**`article_to_markdown(article, social_snippets) → str`**

Erzeugt einen Markdown-String mit folgender Struktur:
```
# {title}
_{lead}_
---
## {section.heading}
{section.content}
---
**Meta-Beschreibung:** {meta_description}
---
## Social Media
### LinkedIn / X / Twitter / Newsletter-Teaser
```

**`article_to_pdf(article, social_snippets) → bytes`**

Rendert denselben Inhalt via `fpdf2` als PDF-Bytes:

| Element | Schrift | Größe |
|---------|---------|-------|
| Titel | Helvetica Bold | 20 pt |
| Lead | Helvetica Italic | 12 pt |
| Section-Heading | Helvetica Bold | 14 pt |
| Section-Content | Helvetica Regular | 11 pt |
| Meta-Beschreibung | Helvetica Italic, grau | 10 pt |
| Social Snippets | Neue Seite, Helvetica | 11–12 pt |

**`_slugify(text) → str`**

Normalisiert den Artikel-Titel zu einem dateifreundlichen Slug (ASCII, Kleinbuchstaben, Bindestriche). Wird für den Dateinamen der Downloads verwendet.

**Abhängigkeit:** `fpdf2>=2.7.0` (Pure-Python, keine Systemabhängigkeiten wie LaTeX oder Ghostscript).

---

## 4. Pipeline-Orchestratoren

### 4.1 Ideen-Pipeline (`pipeline.py`)

**Einstiegspunkt:** `run(status_callback, token_callback) → PipelineResult`

**Ablauf:**

```
Step 1: Parallel-Datenabruf (7 Threads, Timeout 45s gesamt)
        ├── GA4 (7 Tage)
        ├── GA4 (90 Tage)
        ├── GSC Queries (7 Tage)
        ├── GSC Queries (90 Tage)
        ├── GSC Seiten-Positionen (7 Tage)
        ├── RSS-Feeds
        └── Google Trends (Schweiz)

Step 2: Website-Crawler (sequenziell, top 10 GA4-Seiten)

Step 3: Agent 1 – Analyst
Step 4: Agent 2 – Trend-Scout
Step 5: Agent 3 – Stratege
Step 6: Agent 4 – Redakteur

Step 7: Persistenz (ideas_history.json)
```

**Parallelität:** `concurrent.futures.ThreadPoolExecutor(max_workers=7)`. Alle 7 Datenabrufe laufen gleichzeitig. Deadline-basiertes Timeout: 45 Sekunden gesamt. Einzelne Fehler werden als Warnungen in `result.errors` gesammelt, stoppen aber nicht die Pipeline.

**Streaming:** Agenten 1–3 unterstützen Token-Streaming über `token_callback(phase, accumulated_text)`. Der UI-Bereich zeigt den laufenden Agent-Output in Echtzeit an (max. 800 Zeichen tail).

**Ideen-Persistenz:** `_save_ideas_history(ideas)` hängt nach jeder erfolgreichen Generierung einen Eintrag an `data/ideas_history.json` an. Retention: maximal 30 Einträge (älteste werden gelöscht). Fehler bei der Persistenz werden still ignoriert (non-critical).

---

### 4.2 Artikel-Pipeline (`content_pipeline.py`)

**Einstiegspunkt:** `run(idea, rss_articles, gsc_queries, status_callback, target_words) → ContentResult`

**Revision-Loop:**
```
Researcher (einmalig)
    │
    └─► Writer → Fact-Checker → Evaluator ─► passed=True → Social-Writer → Ende
                       ▲              │
                       └── feedback ──┘ (passed=False, max. 2 Wiederholungen)
```

Max. Durchläufe: `MAX_REVISION_LOOPS + 1` (Standard: 3 Durchläufe total).
Social-Writer wird nur ausgeführt, wenn der Artikel die Evaluierung besteht.
Fehler in einzelnen Schritten werden in `result.errors` geloggt; der Writer-Fehler bricht die Loop ab, Fact-Checker- und Evaluator-Fehler führen zu Fallback-Werten.

---

### 4.3 Bewertungs-Pipeline (`evaluation_pipeline.py`)

**Einstiegspunkt:** `run(idea_title, idea_desc, rss_articles, ga4_pages, gsc_queries, status_callback) → EvaluationResult`

**Ablauf:**
1. RSS-Abruf (falls nicht aus vorheriger Pipeline-Ausführung vorhanden)
2. Dynamische Google News-Suche nach Ideen-Titel
3. Agent: Kontext-Suche (findet relevante Datenpunkte)
4. Agent: Ideen-Bewertung (Urteil, Score, Pros/Cons)

**Datenstrategie:** Wenn `rss_articles`, `ga4_pages`, `gsc_queries` aus einer vorherigen Pipeline-Ausführung übergeben werden, werden diese direkt genutzt (kein erneuter API-Aufruf). Nur RSS wird bei Bedarf frisch abgerufen.

---

## 5. Alle Agenten im Detail

### Ideen-Pipeline

#### Agent 1: Analyst (`agents/analyst.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Datengetriebener Content-Analyst |
| **Input** | GA4 7T, GA4 90T, GSC Queries 7T, GSC Queries 90T, GSC Seitenränge |
| **Output** | Strukturierter Markdown-Text mit Erkenntnissen |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.3 |
| **Streaming** | Ja |

**Aufgaben laut Prompt:**
1. 3–5 performante Themenfelder (hohe Views + Engagement)
2. 3–5 Content-Lücken (hohe Impressionen, CTR < 3%)
3. Fast-Ranker (Seiten Position 4–15)
4. Evergreen vs. Kurzfrist-Trends (7T vs. 90T-Vergleich)
5. Übergreifende Suchanfrage-Muster

---

#### Agent 2: Trend-Scout (`agents/trend_scout.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Wirtschaftsjournalist und Trend-Scout |
| **Input** | RSS-Artikel (max. 40) |
| **Output** | Strukturierter Markdown-Text: Top 10 Wirtschaftsthemen |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.3 |
| **Streaming** | Ja |

**Aufgaben laut Prompt:**
1. Top-10-Themen filtern und gruppieren
2. Für jedes Thema: Kurztitel, Relevanz-Begründung, Quelle

---

#### Agent 3: Stratege (`agents/strategist.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Content-Stratege |
| **Input** | Analyst-Output (str), Trend-Scout-Output (str), Crawl-Summaries (str) |
| **Output** | `IDEAS_COUNT` Ideen-Konzepte als strukturierter Text |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.5 |
| **Streaming** | Ja |

Pro Idee im Output:
- Thema/Konzept (kein fertiger Titel)
- Kernbotschaft
- Daten-Basis (Signale)
- Typ: Neuer Artikel oder `[UPDATE]`

Wenn Crawl-Summaries vorhanden: Duplikate werden explizit vermieden, Update-Kandidaten markiert.

---

#### Agent 4: Redakteur (`agents/editor.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Erfahrener digitaler Redakteur |
| **Input** | Strategen-Output (str), RSS-Artikel (list, für Link-Referenzen) |
| **Output** | JSON: `{"ideas": [...]}` |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.6 |
| **Response-Format** | `json_object` |
| **Streaming** | Nein |

**Output-Schema pro Idee:**
```json
{
  "title": "string (10-15 Wörter)",
  "why_now": "string (2-3 Sätze)",
  "category": "string (z.B. 'Geldpolitik')",
  "signals": {
    "ga4": "string (Beobachtung → Begründung)",
    "gsc": "string (Beobachtung → Begründung)",
    "rss": "string (Beobachtung → Begründung)"
  },
  "rss_links": [
    {"title": "string", "url": "string", "source": "string"}
  ],
  "score": "A|B|C"  // nach-hoc berechnet (nicht im Prompt)
}
```

**Score-Berechnung (post-processing):** Nach Erhalt der LLM-Antwort berechnet `_compute_score()` den Score anhand der befüllten Signal-Felder. Anschliessend werden die Ideen nach Score sortiert (A → B → C).

---

### Artikel-Pipeline

#### Agent 5: Researcher (`agents/researcher.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Präziser Rechercheur |
| **Input** | `idea` (dict), `rss_articles` (list), `gsc_queries` (list) |
| **Output** | Strukturierter Markdown-Text (Research-Notes) |
| **Modell** | `OPENAI_MODEL_PRO` (gpt-5.2) |
| **Temperatur** | 0.2 |

**Output-Abschnitte:** Kernthesen · Belege & Datenpunkte · Leserfragen (aus GSC) · Empfohlene Artikel-Struktur · Relevante Quellen

Kein externer API-Aufruf – arbeitet ausschliesslich mit den übergebenen Daten.

---

#### Agent 6: Writer (`agents/writer.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Wirtschaftsjournalist |
| **Input** | `idea`, `research_notes`, `brand_voice`, `forbidden_phrases`, `target_words`, `revision_feedback?` |
| **Output** | JSON-Artikel-Objekt |
| **Modell** | `OPENAI_MODEL_PRO` (gpt-5.2) |
| **Temperatur** | 0.7 |
| **Response-Format** | `json_object` |

**Output-Schema:**
```json
{
  "title": "string",
  "lead": "string (2-3 Sätze)",
  "sections": [
    {"heading": "string", "content": "string (Markdown: Fett, Listen, Absätze)"}
  ],
  "meta_description": "string (max. 160 Zeichen)"
}
```

Bei `revision_feedback` (Folgedurchlauf): Feedback wird explizit in den Prompt integriert.
Wort-Ziel: ±15% Toleranz um `target_words`.

---

#### Agent 7: Fact-Checker (`agents/fact_checker.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Strenger Fact-Checker |
| **Input** | `article` (dict), `research_notes` (str) |
| **Output** | Korrigiertes Artikel-JSON (gleiche Struktur) |
| **Modell** | `OPENAI_MODEL_PRO` (gpt-5.2) |
| **Temperatur** | 0.1 |
| **Response-Format** | `json_object` |

Research-Notes sind die einzige Wahrheitsquelle. Unbelegte Fakten werden entfernt oder korrigiert. Stil und Struktur bleiben erhalten. Bei fehlenden Keys: Fallback auf Original-Artikel-Werte.

---

#### Agent 8: Evaluator (`agents/evaluator.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Kritischer Chefredakteur |
| **Input** | `article` (dict), `idea` (dict) |
| **Output** | JSON-Bewertungsobjekt |
| **Modell** | `OPENAI_MODEL_PRO` (gpt-5.2) |
| **Temperatur** | 0.3 |
| **Response-Format** | `json_object` |

**Output-Schema:**
```json
{
  "scores": {
    "authentizitaet": 0-100,
    "tiefe": 0-100,
    "klarheit": 0-100,
    "relevanz": 0-100
  },
  "overall": 0-100,     // Ø der 4 Scores (server-seitig neu berechnet zur Sicherheit)
  "passed": true|false, // overall >= EVALUATOR_MIN_SCORE (80)
  "feedback": "string"  // Leer wenn passed=true
}
```

Post-Processing: `overall` und `passed` werden client-seitig neu berechnet (LLM-Antwort als Datenbasis, aber eigene Berechnung ist autoritativ).

---

#### Agent 9: Social-Writer (`agents/social_writer.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Social-Media-Redakteur |
| **Input** | `article` (dict), `idea_title` (str) |
| **Output** | JSON mit 3 Plattform-Texten |
| **Modell** | `OPENAI_MODEL_PRO` (gpt-5.2) |
| **Temperatur** | 0.7 |
| **Response-Format** | `json_object` |

Nur die ersten 3 Artikel-Abschnitte werden im Prompt genutzt (Token-Effizienz).

**Output-Schema:**
```json
{
  "linkedin": "string (~1200 Zeichen, professionell, endet mit Frage/CTA)",
  "twitter": "string (max. 280 Zeichen, max. 1-2 Hashtags)",
  "newsletter_teaser": "string (2 Sätze)"
}
```

---

### Bewertungs-Pipeline

#### Agent 10: Kontext-Agent (`agents/idea_context.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Daten-Rechercheur |
| **Input** | `idea_title`, `idea_desc`, `rss_articles`, `ga4_pages`, `gsc_queries` |
| **Output** | Strukturierter Markdown-Text |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.3 |

**Output-Abschnitte:** Relevante RSS-Artikel · GA4-Signale · GSC-Signale · Fazit (Datenlage-Bewertung)

---

#### Agent 11: Bewertungs-Agent (`agents/idea_evaluator.py`)
| Attribut | Wert |
|----------|------|
| **Rolle** | Erfahrener Content-Stratege |
| **Input** | `idea_title`, `idea_desc`, `context` (Kontext-Agent-Output) |
| **Output** | JSON-Bewertungsobjekt |
| **Modell** | `OPENAI_MODEL` (gpt-5.2) |
| **Temperatur** | 0.4 |
| **Response-Format** | `json_object` |

**Output-Schema:**
```json
{
  "verdict": "Empfohlen|Mit Vorbehalt|Nicht empfohlen",
  "score": 0-100,
  "pros": ["string", ...],
  "cons": ["string", ...],
  "recommendation": "string"
}
```

---

## 6. Datenmodelle

### `PipelineResult` (`pipeline.py`)
```python
@dataclass
class PipelineResult:
    ideas: list[dict]          # Fertige Ideen (Editor-Output)
    analyst_output: str        # Rohtext Agent 1
    trend_scout_output: str    # Rohtext Agent 2
    strategist_output: str     # Rohtext Agent 3
    errors: list[str]          # Gesammelte Fehler/Warnungen
    ga4_pages: list[dict]      # GA4 7-Tage-Daten
    gsc_queries: list[dict]    # GSC Queries 7-Tage
    rss_articles: list[dict]   # RSS-Artikel
    gsc_pages: list[dict]      # GSC Seitenränge
    ga4_pages_long: list[dict] # GA4 90-Tage-Daten
    gsc_queries_long: list[dict] # GSC Queries 90-Tage
    crawled_pages: list[dict]  # Website-Crawler-Ergebnisse
    fetched_at: datetime | None
```

### `ContentResult` (`content_pipeline.py`)
```python
@dataclass
class ContentResult:
    article: dict          # Fertiger Artikel (Writer-Output, fact-checked)
    evaluation: dict       # Evaluator-Output mit Scores
    research_notes: str    # Researcher-Output (Rohtext)
    revision_count: int    # Anzahl Überarbeitungsrunden (0 = kein Revision)
    social_snippets: dict  # Social-Writer-Output
    errors: list[str]
```

### `EvaluationResult` (`evaluation_pipeline.py`)
```python
@dataclass
class EvaluationResult:
    verdict: str       # "Empfohlen" | "Mit Vorbehalt" | "Nicht empfohlen"
    score: int         # 0–100
    pros: list[str]
    cons: list[str]
    recommendation: str
    context_notes: str  # Kontext-Agent-Rohtext (für show_details)
    errors: list[str]
```

---

## 7. Konfiguration (`config.py`)

| Konstante | Typ | Standard | Beschreibung |
|-----------|-----|---------|--------------|
| `RSS_FEEDS` | `list[dict]` | 4 Feeds | Definierte RSS-Quellen (`name`, `url`) |
| `ANALYTICS_DAYS_BACK` | `int` | `7` | Kurzfristiger GA4/GSC-Zeitraum |
| `ANALYTICS_DAYS_LONG` | `int` | `90` | Langfristiger Zeitraum (Evergreen-Vergleich) |
| `CRAWL_TOP_PAGES` | `int` | `10` | Anzahl GA4-Seiten für Website-Crawler |
| `IDEAS_COUNT` | `int` | `5` | Anzahl zu generierender Ideen |
| `TRENDS_GEO` | `str` | `"CH"` | Region für Google Trends (ISO-3166-Alpha-2) |
| `TRENDS_LIMIT` | `int` | `20` | Anzahl trendender Keywords |
| `RSS_MAX_ITEMS_PER_FEED` | `int` | `15` | Maximale RSS-Artikel pro Feed |
| `OPENAI_MODEL` | `str` | `"gpt-5.2"` | Modell für Ideen-Pipeline-Agenten |
| `OPENAI_MODEL_PRO` | `str` | `"gpt-5.2"` | Modell für Artikel-Pipeline-Agenten |
| `ARTICLE_TARGET_WORDS` | `int` | `1200` | Standard-Zielwortanzahl für Artikel |
| `MAX_REVISION_LOOPS` | `int` | `2` | Max. Überarbeitungsrunden nach Erstdraft |
| `EVALUATOR_MIN_SCORE` | `int` | `80` | Mindest-Score für bestandene Bewertung |
| `BRAND_VOICE` | `str` | – | Schreibstil-Anweisung (mehrzeilig) |
| `FORBIDDEN_PHRASES` | `list[str]` | 10 Phrasen | Verbotene Formulierungen für Writer-Agent |

**Aktuelle `BRAND_VOICE`:**
```
Sachlich, direkt und faktenbasiert. Komplexe Wirtschaftsthemen
verständlich und ohne Jargon erklären. Schweizer Perspektive
wo relevant. Keine werbliche Sprache, kein Eigenlob.
```

---

## 8. Umgebungsvariablen

| Variable | Pflicht | Beschreibung |
|----------|---------|--------------|
| `OPENAI_API_KEY` | Ja | OpenAI API-Key |
| `GA4_PROPERTY_ID` | Nein* | Google Analytics 4 Property-ID (reine Zahl) |
| `GSC_SITE_URL` | Nein* | Google Search Console Site-URL (vollständige URL inkl. Protokoll) |
| `GOOGLE_CREDENTIALS_FILE` | Nein** | Pfad zur Service-Account-JSON-Datei (Standard: `"credentials.json"`) |
| `GOOGLE_CREDENTIALS_JSON` | Nein** | Inhalt der Service-Account-JSON-Datei (für Streamlit Cloud / Secrets) |

\* Ohne GA4/GSC-Credentials läuft die App, jedoch ohne Google-Daten. RSS-basierte Ideen werden trotzdem generiert.
\*\* Eine der beiden Google-Credentials-Varianten ist erforderlich, wenn GA4/GSC-Daten genutzt werden sollen.

**Streamlit Cloud:** `st.secrets` wird beim App-Start in `os.environ` überführt. TOML-Sektionen werden als JSON-String serialisiert. Damit können Credentials direkt als Secret hinterlegt werden.

---

## 9. Ideen-Scoring

### Algorithmus (`agents/editor.py → _compute_score`)

```python
def _compute_score(signals: dict) -> str:
    count = sum(
        1 for v in (signals.get("ga4"), signals.get("gsc"), signals.get("rss"))
        if v  # Nicht-leerer String = Signal vorhanden
    )
    if count >= 3:
        return "A"
    if count == 2:
        return "B"
    return "C"
```

| Score | Bedingung | Bedeutung |
|-------|-----------|-----------|
| `A` | Alle 3 Signale befüllt | Höchste Datenkonfidenz |
| `B` | Genau 2 Signale befüllt | Gute Datenkonfidenz |
| `C` | 0 oder 1 Signal befüllt | Niedrige Datenkonfidenz |

### Sortierung
```python
score_order = {"A": 0, "B": 1, "C": 2}
result.sort(key=lambda x: score_order.get(x.get("score", "C"), 2))
```

A-Ideen erscheinen in der UI immer zuerst, C-Ideen zuletzt.

---

## 10. Ideen-Persistenz

**Datei:** `data/ideas_history.json`
**Format:** JSON-Array mit maximal 30 Einträgen

```json
[
  {
    "generated_at": "2026-02-26T14:30:00.123456",
    "ideas": [
      {
        "title": "string",
        "why_now": "string",
        "category": "string",
        "signals": {"ga4": "string", "gsc": "string", "rss": "string"},
        "rss_links": [{"title": "string", "url": "string", "source": "string"}],
        "score": "A|B|C"
      }
    ]
  },
  ...
]
```

**Retention-Policy:** Bei jedem Schreiben wird `history[-30:]` genommen – älteste Einträge werden automatisch verworfen.

**Fehlerverhalten:** `_save_ideas_history` ist in einem `try/except` gewrappt und silent-fails – ein Persistenz-Fehler unterbricht nie die Pipeline.

**Laden:** `load_ideas_history() → list[dict]` liest die Datei direkt aus. Bei fehlender Datei oder Parse-Fehler: leere Liste.

**UI:** Die Sidebar zeigt die letzten 5 Generierungen (neueste zuerst) mit Zeitstempel, Ideen-Anzahl und Score-Badges.

---

## 11. Vollständiges Data-Flow-Diagramm

```
                    UMGEBUNGSVARIABLEN
                    ─────────────────
         OPENAI_API_KEY  GA4_PROPERTY_ID  GSC_SITE_URL
         GOOGLE_CREDENTIALS_FILE / GOOGLE_CREDENTIALS_JSON
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE.RUN()                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Parallel-Datenabruf (ThreadPoolExecutor, 7 Threads) │  │
│  │                                                      │  │
│  │  google_analytics.py          rss_reader.py          │  │
│  │  fetch_top_pages(7T)  ──┐  ┌── fetch_rss_articles()  │  │
│  │  fetch_top_pages(90T) ──┤  │                         │  │
│  │                         │  │  search_console.py      │  │
│  │  fetch_top_queries(7T) ─┤  ├── fetch_top_queries(7T) │  │
│  │  fetch_top_queries(90T)─┤  ├── fetch_top_queries(90T)│  │
│  │  fetch_top_pages_by_pos─┤  └── (gsc pages)           │  │
│  │                         │                            │  │
│  │  google_trends.py       │                            │  │
│  │  fetch_trending_topics──┘                            │  │
│  │                                                      │  │
│  │  Return: list[dict] je Quelle    Timeout: 45s        │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  content_crawler.py                                  │  │
│  │  crawl_top_pages(ga4_pages, base_url, limit=10)      │  │
│  │  → list[dict]: {url, title, summary, word_count,     │  │
│  │                 estimated_date, page_views, error}   │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/analyst.py  (temp=0.3, streaming)            │  │
│  │  Input:  ga4_7T, gsc_queries_7T, gsc_pages,          │  │
│  │          ga4_90T, gsc_queries_90T                    │  │
│  │  Output: str (Markdown, Analyst-Erkenntnisse)        │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/trend_scout.py  (temp=0.3, streaming)        │  │
│  │  Input:  rss_articles (max. 40)                      │  │
│  │  Output: str (Markdown, Top-10-Themen)               │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/strategist.py  (temp=0.5, streaming)         │  │
│  │  Input:  analyst_output, trend_scout_output,         │  │
│  │          crawl_summaries (formatted str)             │  │
│  │  Output: str (Markdown, IDEAS_COUNT Ideen-Konzepte)  │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/editor.py  (temp=0.6, json_object)           │  │
│  │  Input:  strategist_output, rss_articles (max. 30)   │  │
│  │  Output: list[dict] (Ideen mit title/why_now/        │  │
│  │          category/signals/rss_links/score)           │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│              _save_ideas_history()                          │
│              → data/ideas_history.json (max. 30 Runs)      │
│                                                             │
│  Return: PipelineResult                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (Benutzer wählt Idee)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONTENT_PIPELINE.RUN()                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  agents/researcher.py  (temp=0.2)                    │  │
│  │  Input:  idea, rss_articles, gsc_queries             │  │
│  │  Output: str (Research-Notes: Markdown)              │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  REVISION-LOOP  (max. MAX_REVISION_LOOPS+1 = 3x)     │  │
│  │                                                      │  │
│  │  agents/writer.py  (temp=0.7, json_object)           │  │
│  │  Input:  idea, research_notes, brand_voice,          │  │
│  │          forbidden_phrases, target_words,            │  │
│  │          revision_feedback? (str|None)               │  │
│  │  Output: dict {title, lead, sections, meta_desc}     │  │
│  │               │                                      │  │
│  │  agents/fact_checker.py  (temp=0.1, json_object)     │  │
│  │  Input:  article, research_notes                     │  │
│  │  Output: dict (korrigiertes Artikel-JSON)            │  │
│  │               │                                      │  │
│  │  agents/evaluator.py  (temp=0.3, json_object)        │  │
│  │  Input:  article, idea                               │  │
│  │  Output: dict {scores, overall, passed, feedback}    │  │
│  │               │                                      │  │
│  │          passed=True? ─── Ja → Exit Loop             │  │
│  │               │                                      │  │
│  │          Nein: revision_feedback → Writer (nächster  │  │
│  │          Durchlauf) bis max. Loops erreicht          │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │ (nur wenn passed=True)         │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/social_writer.py  (temp=0.7, json_object)    │  │
│  │  Input:  article (sections[:3]), idea_title          │  │
│  │  Output: dict {linkedin, twitter, newsletter_teaser} │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  Return: ContentResult                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (Artikel in app.py dargestellt)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      EXPORT (export.py)                     │
│                                                             │
│  article_to_markdown(article, social_snippets) → str        │
│  article_to_pdf(article, social_snippets) → bytes (fpdf2)   │
│  _slugify(title) → str  (für Dateinamen)                    │
│                                                             │
│  UI: st.download_button "📄 Markdown" + "🖨️ PDF"            │
│      st.button "🌐 CMS importieren" (disabled)              │
└─────────────────────────────────────────────────────────────┘

                  (parallel, unabhängig von Artikel-Pipeline)
┌─────────────────────────────────────────────────────────────┐
│                EVALUATION_PIPELINE.RUN()                    │
│                                                             │
│  RSS-Fetch (falls kein Cache) + Google News-Suche           │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/idea_context.py  (temp=0.3)                  │  │
│  │  Input:  idea_title, idea_desc, rss, ga4, gsc        │  │
│  │  Output: str (Kontext-Markdown)                      │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │  agents/idea_evaluator.py  (temp=0.4, json_object)   │  │
│  │  Input:  idea_title, idea_desc, context              │  │
│  │  Output: dict {verdict, score, pros, cons,           │  │
│  │                recommendation}                       │  │
│  └─────────────────────────┬────────────────────────────┘  │
│                            │                                │
│  Return: EvaluationResult                                   │
└─────────────────────────────────────────────────────────────┘
```

---

*Stand: Februar 2026 – zuletzt aktualisiert: Artikel-Export (MD/PDF), Google Trends, 7-Thread-Parallelität*
