# Content-Ideen-Generator – Funktionen & Nutzen

*Dokumentation für Redaktion, Marketing und nicht-technische Entscheider*

---

## 1. Was ist der Content-Ideen-Generator?

Redaktionsteams verbringen täglich wertvolle Zeit damit, Themen zu suchen und zu priorisieren – oft ohne verlässliche Datenbasis. Der **Content-Ideen-Generator** löst dieses Problem: Er kombiniert automatisch die echten Nutzungsdaten der eigenen Website (welche Seiten werden gelesen, wonach suchen Leser) mit aktuellen Wirtschaftsnachrichten aus deutschsprachigen Medien und schlägt daraus konkrete, begründete Artikel-Ideen vor. Jede Empfehlung ist mit einem Qualitäts-Score bewertet und direkt in fertige Artikel umsetzbar.

---

## 2. Die zwei Hauptfunktionen

Das Tool bietet zwei voneinander unabhängige, aber aufeinander aufbauende Funktionen:

### Funktion 1: Ideen generieren
Auf Knopfdruck analysiert das System alle verfügbaren Datenquellen und liefert eine priorisierte Liste von Artikel-Ideen – mit Begründung, Kategorie, Qualitäts-Score und den zugrundeliegenden Datenpunkten.

### Funktion 2: Artikel erstellen
Für jede generierte Idee kann per Klick ein vollständiger, redaktionell aufbereiteter Artikel erstellt werden – inklusive Faktenprüfung, Qualitätsbewertung und fertigen Social-Media-Texten für LinkedIn, X/Twitter und Newsletter.

Zusätzlich gibt es eine dritte Funktion: **Eigene Ideen prüfen** – Redakteur:innen können selbst eingebrachte Themen gegen die verfügbaren Daten testen lassen.

---

## 3. Datenquellen

Das System bezieht Informationen aus vier Quellen, die automatisch vor jeder Ideen-Generierung abgerufen werden:

### Google Analytics 4 (GA4)
Die eigenen Seitenaufruf-Statistiken der Website. Das System analysiert, welche Artikel in den letzten 7 und 90 Tagen am meisten gelesen wurden und wie stark sich Leser damit beschäftigt haben. Daraus lassen sich Evergreen-Themen (dauerhaft gefragt) von kurzfristigen Trends unterscheiden.

### Google Search Console (GSC)
Zeigt, nach welchen Begriffen Leser auf Google suchen und dann auf die eigene Website klicken – oder eben nicht klicken. Hohe Suchanfragen bei niedrigen Klicks sind ein klares Signal: Leser suchen aktiv nach diesem Thema, aber die eigene Website liefert noch keine befriedigende Antwort. Das System erkennt auch, welche eigenen Seiten kurz vor einem Top-3-Rang in der Google-Suche stehen (sogenannte "Fast-Ranker") und mit einem gezielten Update nach oben katapultiert werden könnten.

### RSS-Feeds (Wirtschaftsmedien)
Aktuelle Artikel aus deutschsprachigen Wirtschaftsmedien (NZZ, SRF, Tages-Anzeiger sowie Google News Wirtschaft Schweiz) werden täglich eingelesen. Das System filtert die 10 relevantesten Themen heraus und verbindet sie mit den eigenen Daten – so entstehen Ideen, die sowohl aktuell als auch für die eigene Leserschaft relevant sind.

### Website-Crawler (eigene Inhalte)
Die meistbesuchten eigenen Seiten werden automatisch analysiert und zusammengefasst. Das verhindert, dass bereits gut abgedeckte Themen doppelt vorgeschlagen werden. Stattdessen erkennt das System veraltete Artikel, die ein Update benötigen, und schlägt neue Blickwinkel auf bereits behandelte Themen vor.

---

## 4. Wie die Ideen-Generierung funktioniert: 4 KI-Agenten

Die Ideen-Generierung läuft vollautomatisch durch vier spezialisierte KI-Agenten, die sequenziell arbeiten und ihre Erkenntnisse weitergeben:

### Agent 1: Analyst
**Was er tut:** Wertet die GA4- und GSC-Daten aus.
**Was er erkennt:**
- Themen mit hoher Leser-Nachfrage (viele Aufrufe + hohes Engagement)
- Keywords mit vielen Google-Suchanfragen, aber schlechter eigener Sichtbarkeit (Content-Lücken)
- Fast-Ranker: eigene Seiten, die knapp vor einem Top-Suchergebnis stehen
- Dauerhaft gefragte Themen (Evergreen) vs. kurzfristige Trends

### Agent 2: Trend-Scout
**Was er tut:** Analysiert die aktuellen Nachrichten aus den RSS-Feeds.
**Was er erkennt:** Die 10 wichtigsten Wirtschaftsthemen des Moments, gruppiert nach Oberthemen, mit Quellenangabe.

### Agent 3: Stratege
**Was er tut:** Kombiniert die Erkenntnisse von Analyst und Trend-Scout, unter Berücksichtigung der bestehenden Website-Inhalte.
**Was er liefert:** Konkrete Ideen-Konzepte mit Kernbotschaft und Datenbasis – keine generischen Themen, sondern spezifische Artikel-Ansätze.

### Agent 4: Redakteur
**Was er tut:** Verfeinert die Ideen-Konzepte zu konkreten Empfehlungen.
**Was er liefert:** Für jede Idee einen klickwürdigen Titel, eine kurze Aktualitätsbegründung, eine Themenkategorie, konkrete Datenpunkte und einen Qualitäts-Score.

---

## 5. Was eine fertige Idee enthält

Jede Ideen-Empfehlung wird mit folgenden Informationen dargestellt:

| Feld | Beschreibung |
|------|--------------|
| **Titel** | Ein formulierter Artikel-Titel, auf den Leser klicken würden |
| **Warum jetzt?** | 2–3 Sätze, warum das Thema genau jetzt relevant ist |
| **Kategorie** | z.B. Geldpolitik, Investitionen, Konjunktur, Unternehmen, Steuern & Recht |
| **Score A / B / C** | Qualitätsbewertung nach Anzahl der Datensignale (s. unten) |
| **Daten-Signale** | Welche GA4-Daten, GSC-Daten und Nachrichten diese Idee stützen |
| **Quellartikel** | Links zu den RSS-Artikeln, die das Thema anstossen |

### Score-System (A / B / C)
Das Score-System zeigt auf einen Blick, wie gut eine Idee durch Daten belegt ist:

- **Score A (grün):** Alle drei Signalquellen (GA4, GSC, RSS) bestätigen das Thema → höchste Priorität
- **Score B (gelb):** Zwei von drei Signalquellen stützen die Idee → gute Priorität
- **Score C (rot):** Nur eine Signalquelle → eher opportunistische Idee, geringere Datengrundlage

Die Ideen werden automatisch nach Score sortiert: A-Ideen erscheinen zuerst.

---

## 6. Artikel erstellen: 5 KI-Agenten

Sobald eine Idee ausgewählt ist, übernimmt die Artikel-Pipeline. Vier Agenten arbeiten in einem Qualitätskreislauf, ein fünfter erstellt abschliessend Social-Media-Texte:

### Agent 1: Researcher
Extrahiert aus den verfügbaren Daten (RSS-Artikel, GSC-Suchanfragen) konkrete Fakten, Zahlen, Zitate und Quellenhinweise. Er erfindet keine Fakten und verlässt sich ausschliesslich auf vorhandene Daten.

### Agent 2: Writer
Verfasst auf Basis der Research-Notes einen vollständigen Artikel. Er hält sich an die hinterlegte **Brand Voice** (sachlich, direkt, faktenbasiert; Schweizer Perspektive wo relevant; keine Werbesprache) und vermeidet definierte **verbotene Formulierungen** ("revolutionär", "synergetisch", etc.).

Das Artikel-Format ist wählbar:
- Kurzmeldung (~300 Wörter)
- Standardartikel (~1200 Wörter)
- Analyse (~2500 Wörter)

### Agent 3: Fact-Checker
Prüft jeden faktischen Anspruch im Entwurf gegen die Research-Notes. Korrektheit geht vor Stil: Unbelegte Aussagen werden entfernt oder korrigiert.

### Agent 4: Evaluator
Bewertet den Artikel nach vier Qualitätsdimensionen (je 0–100 Punkte):
- **Authentizität**: Sachlicher, glaubwürdiger Ton – keine Werbesprache
- **Tiefe**: Konkrete Fakten statt Allgemeinplätze
- **Klarheit**: Verständliche Struktur, klare Argumentation
- **Relevanz**: Passt der Artikel zur Idee, ist er aktuell?

Bei einem Gesamtwert unter 80 geht der Artikel automatisch zurück an den Writer zur Überarbeitung – maximal 2 Runden. Erst bei bestandener Bewertung wird fortgefahren.

### Agent 5: Social-Writer
Erstellt aus dem finalen Artikel automatisch drei fertige Social-Media-Texte:
- **LinkedIn:** ~1200 Zeichen, professionell, mit Frage oder Call-to-Action am Ende
- **X / Twitter:** Max. 280 Zeichen, prägnant, maximal 1–2 Hashtags
- **Newsletter-Teaser:** 2 Sätze, neugierig machend

---

## 7. Eigene Ideen prüfen

Redakteur:innen können auch selbst eingebrachte Ideen gegen die verfügbaren Daten testen – ohne eine vollständige Ideen-Generierung starten zu müssen.

**So funktioniert es:**
1. Ideen-Titel eingeben (optional: kurze Beschreibung)
2. Auf "Prüfen" klicken
3. Zwei KI-Agenten analysieren die Idee:
   - Ein **Kontext-Agent** sucht passende Signale in RSS-Artikeln, GA4 und GSC
   - Ein **Bewertungs-Agent** gibt ein Urteil ab

**Was zurückkommt:**
- **Urteil:** Empfohlen / Mit Vorbehalt / Nicht empfohlen
- **Score:** 0–100 Punkte
- **Dafür spricht:** Liste der positiven Signale
- **Dagegen spricht:** Liste der Gegenargumente
- **Empfehlung:** Konkreter Handlungsvorschlag

*Hinweis:* Wenn zuvor bereits Ideen generiert wurden, verwendet die Prüfung die bereits geladenen Daten und ist entsprechend schneller.

---

## 8. Smarte Zusatzfunktionen

### Fast-Ranker-Erkennung
Das System identifiziert automatisch eigene Seiten, die bei Google auf Position 4–15 ranken. Diese Seiten sind knapp vor einem Top-3-Platz und hätten mit einem gezielten Content-Update das höchste Potential für mehr organischen Traffic. Fast-Ranker werden in der Oberfläche separat aufgelistet.

### Evergreen-Erkennung
Durch den Vergleich von 7-Tage- und 90-Tage-Daten erkennt das System, welche Themen dauerhaft gefragt sind (Evergreen) und welche gerade einen temporären Nachrichtenanlass haben (Trend). Diese Information fliesst in die Ideen-Begründungen ein.

### Ideen-Verlauf
Alle bisher generierten Ideen-Sets werden automatisch gespeichert. Im linken Bereich der Oberfläche sind die letzten 5 Generierungen mit Datum, Uhrzeit und Score-Übersicht abrufbar. So lassen sich frühere Ideen wiederfinden oder Entwicklungen im Zeitverlauf nachvollziehen.

### Bookmarks
Einzelne Ideen können gemerkt werden – mit optionaler Notiz ("Für Anna / bis Do. / Winkel: Konsument"). Gemerkte Ideen erscheinen im linken Bereich und bleiben während der Sitzung erhalten.

---

## 9. Was konfiguriert werden kann

Das System ist auf spezifische Bedürfnisse anpassbar:

| Einstellung | Was sie bewirkt |
|-------------|-----------------|
| **Brand Voice** | Definiert den Schreibstil für generierte Artikel (z.B. sachlich, Schweizer Perspektive) |
| **Verbotene Formulierungen** | Liste von Phrasen, die der Writer nie verwenden darf |
| **RSS-Feeds** | Welche Nachrichtenquellen eingelesen werden (aktuell: NZZ, SRF, Tages-Anzeiger, Google News CH) |
| **Anzahl Ideen** | Wie viele Ideen pro Generierung erstellt werden (Standard: 5) |
| **Analysezeitraum** | Wie viele Tage zurück GA4 und GSC-Daten abgerufen werden (7 Tage kurzfristig, 90 Tage langfristig) |
| **Artikel-Zielumfang** | Standard-Wortanzahl für generierte Artikel (Standard: 1200 Wörter) |
| **Qualitätsschwelle** | Ab welchem Score ein Artikel als "bestanden" gilt (Standard: 80/100) |

---

## 10. Datenfluss-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│                    DATENQUELLEN                         │
│  GA4 (7T + 90T) │ GSC (7T + 90T + Seiten) │ RSS-Feeds │
└────────────────────────────┬────────────────────────────┘
                             │ parallel
                             ▼
┌─────────────────────────────────────────────────────────┐
│               WEBSITE-CRAWLER                           │
│         Top-10-Seiten werden analysiert                 │
└────────────────────────────┬────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   ANALYST       │  GA4 + GSC auswerten
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  TREND-SCOUT    │  RSS-Feeds filtern
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   STRATEGE      │  Ideen konzipieren
                    └────────┬────────┘  (+ Website-Kontext)
                             │
                    ┌────────▼────────┐
                    │   REDAKTEUR     │  Titel + Score + Signale
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ IDEEN-LISTE     │  Sortiert A → B → C
                    └────────┬────────┘
                             │ (auf Klick)
        ┌────────────────────▼────────────────────┐
        │           ARTIKEL-PIPELINE              │
        │  Researcher → Writer → Fact-Checker     │
        │       → Evaluator (max. 2 Runden)       │
        │       → Social-Writer                   │
        └─────────────────────────────────────────┘
```

---

*Stand: Februar 2026*
