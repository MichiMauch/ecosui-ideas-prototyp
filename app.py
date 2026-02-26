"""
Content-Ideen-Generator – Streamlit App

Zeigt 10 KI-generierte Content-Ideen basierend auf:
  - Google Analytics 4 (Top-Seiten & Engagement)
  - Google Search Console (Keywords & CTR-Lücken)
  - RSS-Feeds von Wirtschaftsmedien

Zusätzlich: Vollständige Artikel per "✍️ Artikel erstellen"-Button generieren.
"""

import json
import os

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Streamlit Cloud: st.secrets → os.environ (Pipeline nutzt os.getenv)
try:
    for _key, _val in st.secrets.items():
        if _key not in os.environ:
            if isinstance(_val, str):
                os.environ[_key] = _val
            else:
                # TOML-Sektion (z.B. [GOOGLE_CREDENTIALS_JSON]) → JSON-String
                os.environ[_key] = json.dumps(dict(_val))
except Exception:
    pass

from datetime import timedelta

import pipeline
import content_pipeline
import evaluation_pipeline
from config import ANALYTICS_DAYS_BACK


@st.cache_data(ttl=300)
def _check_connections() -> dict:
    """Prüft GA4-, GSC- und RSS-Verbindungen mit echten API-Calls. Gecacht für 5 Minuten."""
    from data.google_analytics import fetch_top_pages
    from data.search_console import fetch_top_queries
    from data.rss_reader import _fetch_feed_raw
    from config import RSS_FEEDS

    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    property_id = os.getenv("GA4_PROPERTY_ID")
    site_url = os.getenv("GSC_SITE_URL")

    ga4_error = None
    try:
        if not property_id:
            raise ValueError("GA4_PROPERTY_ID nicht gesetzt")
        fetch_top_pages(property_id, creds_file, days_back=7, limit=1)
        ga4_ok = True
    except Exception as e:
        ga4_ok = False
        ga4_error = str(e)

    gsc_error = None
    try:
        if not site_url:
            raise ValueError("GSC_SITE_URL nicht gesetzt")
        fetch_top_queries(site_url, creds_file, days_back=7, limit=1)
        gsc_ok = True
    except Exception as e:
        gsc_ok = False
        gsc_error = str(e)

    _display = {"NZZ Wirtschaft": "NZZ", "SRF Wirtschaft": "SRF",
                "Tages-Anzeiger Wirtschaft": "Tagi"}
    rss_status = {}
    for feed in RSS_FEEDS:
        label = _display.get(feed["name"], feed["name"])
        try:
            _fetch_feed_raw(feed["url"])
            rss_status[label] = True
        except Exception:
            rss_status[label] = False

    return {"ga4": ga4_ok, "gsc": gsc_ok, "rss": rss_status,
            "ga4_error": ga4_error, "gsc_error": gsc_error}


st.set_page_config(
    page_title="Content-Ideen-Generator",
    page_icon="💡",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💡 Content-Ideen-Generator")
st.markdown(
    "Generiert 10 datengetriebene Artikel-Ideen basierend auf GA4, "
    "Google Search Console und aktuellen Wirtschafts-News."
)

st.divider()

# ── Sidebar: Status & Details ─────────────────────────────────────────────────
with st.sidebar:
    st.header("ℹ️ Info")

    conn = _check_connections()
    _ic = lambda ok: "🟢" if ok else "🔴"

    st.markdown("**Verbindungsstatus:**")
    lines = [
        f"- {_ic(conn['ga4'])} Google Analytics 4 (letzte 7 Tage)",
        f"- {_ic(conn['gsc'])} Google Search Console (letzte 7 Tage)",
    ]
    for name, ok in conn["rss"].items():
        lines.append(f"- {_ic(ok)} RSS: {name}")
    st.markdown("\n".join(lines))

    if conn.get("ga4_error"):
        st.caption(f"GA4: {conn['ga4_error']}")
    if conn.get("gsc_error"):
        st.caption(f"GSC: {conn['gsc_error']}")

    st.markdown(
        """
**4 KI-Agenten (Ideen):**
1. 🔍 Analyst (GA4 + GSC)
2. 📰 Trend-Scout (RSS)
3. 🧠 Stratege
4. ✏️ Redakteur

**4 KI-Agenten (Artikel):**
1. 🔬 Researcher
2. ✍️ Writer
3. ✅ Fact-Checker
4. 🎯 Evaluator
    """
    )

    st.divider()

    show_details = st.checkbox("Agent-Outputs anzeigen", value=False)

    # ── Gemerkte Ideen ───────────────────────────────────────────────────────
    _bookmarks = st.session_state.get("bookmarks", {})
    if _bookmarks:
        st.divider()
        st.markdown("**🔖 Gemerkte Ideen:**")
        for _bm_title, _bm_data in list(_bookmarks.items()):
            _bm_cat = _bm_data.get("idea", {}).get("category", "")
            _bm_note = _bm_data.get("note", "")
            _col_t, _col_d = st.columns([5, 1])
            with _col_t:
                if _bm_cat:
                    st.caption(_bm_cat)
                st.markdown(f"**{_bm_title}**")
                if _bm_note:
                    st.caption(f"_{_bm_note}_")
            with _col_d:
                if st.button("🗑", key=f"rm_bm_{_bm_title}", help="Entfernen"):
                    del st.session_state.bookmarks[_bm_title]
                    st.rerun()

# ── Session State Initialisation ──────────────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "selected_idea" not in st.session_state:
    st.session_state.selected_idea = None
if "content_result" not in st.session_state:
    st.session_state.content_result = None
if "eval_result" not in st.session_state:
    st.session_state.eval_result = None
if "eval_idea_title" not in st.session_state:
    st.session_state.eval_idea_title = ""
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = {}
if "target_words" not in st.session_state:
    st.session_state.target_words = 1200

# ── Main: Generate Button ──────────────────────────────────────────────────────
col1, col2 = st.columns([1, 3])
with col1:
    generate = st.button("🚀 Ideen generieren", type="primary", use_container_width=True)

# ── Run Ideas Pipeline ────────────────────────────────────────────────────────
if generate:
    # Reset article state when regenerating ideas
    st.session_state.selected_idea = None
    st.session_state.content_result = None

    phase_labels = {
        "analyst":     "🔍 Analyst (GA4 + Search Console)",
        "trend_scout": "📰 Trend-Scout (RSS-Feeds)",
        "strategist":  "🧠 Stratege",
    }

    # st.empty() as outer wrapper so log_area.empty() removes the whole container
    log_area = st.empty()
    with log_area.container(height=300, border=True):
        progress = st.progress(0)
        status_placeholder = st.empty()
        content_placeholder = st.empty()

    steps = [
        "Daten werden geladen (GA4, Search Console, RSS)...",
        "Agent 1/4: Analyst wertet GA4 & Search Console aus...",
        "Agent 2/4: Trend-Scout analysiert RSS-Feeds...",
        "Agent 3/4: Stratege kombiniert Erkenntnisse zu Ideen...",
        "Agent 4/4: Redakteur verfeinert Titel & Begründungen...",
        "Fertig!",
    ]
    step_index = [0]

    def on_status(msg: str):
        status_placeholder.info(f"⏳ {msg}")
        idx = next((i for i, s in enumerate(steps) if s == msg), step_index[0])
        step_index[0] = idx
        progress.progress(min(idx / (len(steps) - 1), 1.0))
        content_placeholder.empty()  # clear previous agent's output on phase switch

    def on_token(phase: str, accumulated_text: str):
        label = phase_labels.get(phase, phase)
        # Always display the tail so the latest text is visible without scrolling
        MAX_CHARS = 800
        if len(accumulated_text) > MAX_CHARS:
            display_text = "…\n\n" + accumulated_text[-MAX_CHARS:]
        else:
            display_text = accumulated_text
        content_placeholder.markdown(f"**{label}**\n\n{display_text}")

    result = pipeline.run(status_callback=on_status, token_callback=on_token)
    st.session_state.pipeline_result = result

    log_area.empty()  # removes the entire container once ideas are ready

# ── Display Ideas (and article button) ────────────────────────────────────────
result = st.session_state.pipeline_result

if result is not None:
    # ── Quelldaten-Sektion ────────────────────────────────────────────────────
    st.subheader("📊 Quelldaten")

    col_ga4, col_gsc, col_rss = st.columns(3)
    col_ga4.metric(
        "Google Analytics 4",
        f"{len(result.ga4_pages)} Seiten" if result.ga4_pages else "Keine Daten",
        delta="✅ Verbunden" if result.ga4_pages else "⚠️ Keine Verbindung",
    )
    col_gsc.metric(
        "Search Console",
        f"{len(result.gsc_queries)} Suchanfragen" if result.gsc_queries else "Keine Daten",
        delta="✅ Verbunden" if result.gsc_queries else "⚠️ Keine Verbindung",
    )
    col_rss.metric(
        "RSS-Feeds",
        f"{len(result.rss_articles)} Artikel" if result.rss_articles else "Keine Daten",
        delta="✅ Geladen" if result.rss_articles else "⚠️ Keine Daten",
    )

    if result.fetched_at:
        date_to = result.fetched_at.date()
        date_from = date_to - timedelta(days=ANALYTICS_DAYS_BACK)
        st.caption(
            f"Zeitraum: {date_from.strftime('%d.%m.%Y')} – {date_to.strftime('%d.%m.%Y')} "
            f"· Abgerufen um {result.fetched_at.strftime('%H:%M')} Uhr"
        )

    with st.expander("📈 GA4-Rohdaten anzeigen"):
        if result.ga4_pages:
            st.dataframe(
                [
                    {
                        "Seite": p["page_title"],
                        "Aufrufe": p["page_views"],
                        "Engagement": f"{p['engagement_rate']}%",
                    }
                    for p in result.ga4_pages
                ],
                use_container_width=True,
            )
        else:
            st.info("Keine GA4-Daten verfügbar (Zugangsdaten prüfen).")

    with st.expander("🔍 Search Console-Rohdaten anzeigen"):
        if result.gsc_queries:
            st.dataframe(
                [
                    {
                        "Suchanfrage": q["query"],
                        "Impressionen": q["impressions"],
                        "Klicks": q["clicks"],
                        "CTR": f"{q['ctr']}%",
                        "Position": q["position"],
                    }
                    for q in result.gsc_queries
                ],
                use_container_width=True,
            )
        else:
            st.info("Keine GSC-Daten verfügbar (Zugangsdaten prüfen).")

    st.divider()

    # ── Errors ────────────────────────────────────────────────────────────────
    if result.errors:
        with st.expander("⚠️ Warnungen / Fehler", expanded=True):
            for err in result.errors:
                st.warning(err)

    # ── Ideas Grid ────────────────────────────────────────────────────────────
    if result.ideas:
        st.subheader(f"✨ {len(result.ideas)} Content-Ideen")

        category_colors = {
            "Geldpolitik": "🔵",
            "Investitionen": "🟢",
            "Konjunktur": "🟡",
            "Unternehmen": "🟠",
            "Steuern & Recht": "🔴",
        }

        for i, idea in enumerate(result.ideas, 1):
            title = idea.get("title", "Kein Titel")
            why_now = idea.get("why_now", "")
            category = idea.get("category", "")
            icon = category_colors.get(category, "⚪")

            signals = idea.get("signals", {})

            with st.container(border=True):
                col_num, col_content = st.columns([0.5, 9.5])
                with col_num:
                    st.markdown(f"### {i}")
                with col_content:
                    if category:
                        st.markdown(f"{icon} `{category}`")
                    st.markdown(f"### {title}")
                    if why_now:
                        st.markdown(f"**Warum jetzt?** {why_now}")

                    # Data signals expander
                    with st.expander("📊 Daten-Signale (warum diese Idee?)"):
                        ga4_signal = signals.get("ga4", "")
                        gsc_signal = signals.get("gsc", "")
                        rss_signal = signals.get("rss", "")
                        rss_links = idea.get("rss_links", [])
                        if ga4_signal:
                            st.markdown(f"**📈 Google Analytics 4**\n\n{ga4_signal}")
                        if gsc_signal:
                            st.markdown(f"**🔍 Google Search Console**\n\n{gsc_signal}")
                        if rss_signal:
                            st.markdown(f"**📰 RSS-Feeds**\n\n{rss_signal}")
                        if rss_links:
                            st.markdown("**🔗 Quellartikel:**")
                            for link in rss_links:
                                st.markdown(f"- [{link['title']}]({link['url']}) — *{link['source']}*")
                        if not any([ga4_signal, gsc_signal, rss_signal]):
                            st.markdown("_Keine Signale verfügbar._")

                    # Format-Auswahl
                    _format_options = {
                        "Kurzmeldung (~300 Wörter)": 300,
                        "Standardartikel (~1200 Wörter)": 1200,
                        "Analyse (~2500 Wörter)": 2500,
                    }
                    _selected_format = st.selectbox(
                        "Artikel-Format",
                        list(_format_options.keys()),
                        index=1,
                        key=f"format_{i}",
                    )
                    _target_words = _format_options[_selected_format]

                    _col_btn, _col_bm = st.columns([3, 1])
                    with _col_btn:
                        if st.button(
                            "✍️ Artikel erstellen",
                            key=f"create_article_{i}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_idea = idea
                            st.session_state.content_result = None
                            st.session_state.target_words = _target_words
                            st.rerun()

                    _is_bookmarked = title in st.session_state.bookmarks
                    with _col_bm:
                        _bm_label = "🔖 Gemerkt" if _is_bookmarked else "🔖 Merken"
                        if st.button(_bm_label, key=f"bm_{i}", use_container_width=True):
                            if _is_bookmarked:
                                del st.session_state.bookmarks[title]
                            else:
                                st.session_state.bookmarks[title] = {"idea": idea, "note": ""}

                    if title in st.session_state.bookmarks:
                        _note = st.text_input(
                            "Notiz",
                            key=f"note_{i}",
                            placeholder="z.B. Für Anna, bis Do. / Winkel: Konsument",
                            label_visibility="collapsed",
                        )
                        st.session_state.bookmarks[title]["note"] = _note

        st.divider()

        # ── Agent Detail Outputs ───────────────────────────────────────────────
        if show_details:
            st.subheader("🔍 Agent-Outputs (Ideen-Pipeline)")
            with st.expander("Agent 1: Analyst (GA4 + GSC)", expanded=False):
                st.markdown(result.analyst_output or "_Keine Daten_")

            with st.expander("Agent 2: Trend-Scout (RSS)", expanded=False):
                st.markdown(result.trend_scout_output or "_Keine Daten_")

            with st.expander("Agent 3: Stratege", expanded=False):
                st.markdown(result.strategist_output or "_Keine Daten_")

    elif not result.errors:
        st.error("Es wurden keine Ideen generiert. Bitte überprüfe die Konfiguration.")

# ── Eigene Idee prüfen ────────────────────────────────────────────────────────
st.divider()
st.subheader("💭 Eigene Idee prüfen")

col_input, col_btn = st.columns([4, 1])
with col_input:
    user_idea_title = st.text_input(
        "Ideen-Titel",
        placeholder="z.B. Warum der Franken 2025 unter Druck gerät",
        label_visibility="collapsed",
    )
user_idea_desc = st.text_area(
    "Beschreibung (optional)",
    placeholder="Kurze Erläuterung der Idee ...",
    height=80,
    label_visibility="collapsed",
)
with col_btn:
    check_btn = st.button(
        "🔍 Prüfen",
        type="primary",
        use_container_width=True,
        disabled=not user_idea_title.strip(),
    )

if check_btn and user_idea_title.strip():
    st.session_state.eval_result = None
    pr = st.session_state.pipeline_result

    eval_status = st.empty()
    eval_result = evaluation_pipeline.run(
        idea_title=user_idea_title,
        idea_desc=user_idea_desc,
        rss_articles=pr.rss_articles if pr else None,
        ga4_pages=pr.ga4_pages if pr else None,
        gsc_queries=pr.gsc_queries if pr else None,
        status_callback=lambda msg: eval_status.info(f"⏳ {msg}"),
    )
    eval_status.empty()
    st.session_state.eval_result = eval_result
    st.session_state.eval_idea_title = user_idea_title

eval_result = st.session_state.eval_result
if eval_result:
    verdict_icon = {
        "Empfohlen": "🟢",
        "Mit Vorbehalt": "🟡",
        "Nicht empfohlen": "🔴",
    }.get(eval_result.verdict, "⚪")

    if eval_result.errors:
        with st.expander("⚠️ Warnungen / Fehler (Ideen-Prüfung)", expanded=True):
            for err in eval_result.errors:
                st.warning(err)

    if eval_result.verdict:
        with st.container(border=True):
            c1, c2 = st.columns([1, 3])
            c1.metric(
                "Bewertung",
                f"{eval_result.score}/100",
                delta=f"{verdict_icon} {eval_result.verdict}",
            )
            c2.markdown(f"**Empfehlung:** {eval_result.recommendation}")

            col_pro, col_con = st.columns(2)
            with col_pro:
                st.markdown("**✅ Dafür spricht:**")
                for p in eval_result.pros:
                    st.markdown(f"- {p}")
            with col_con:
                st.markdown("**⚠️ Dagegen spricht:**")
                for c in eval_result.cons:
                    st.markdown(f"- {c}")

        if show_details and eval_result.context_notes:
            with st.expander("🔍 Kontext-Agent Output", expanded=False):
                st.markdown(eval_result.context_notes)

# ── Article Creation Section ──────────────────────────────────────────────────
selected_idea = st.session_state.selected_idea

if selected_idea is not None:
    st.divider()
    st.subheader(f"✍️ Artikel erstellen: {selected_idea.get('title', '')}")

    # Run content pipeline if not yet done
    if st.session_state.content_result is None:
        pipeline_result = st.session_state.pipeline_result

        rss_articles = pipeline_result.rss_articles if pipeline_result else []
        gsc_queries = pipeline_result.gsc_queries if pipeline_result else []

        content_steps = [
            "Researcher: Fakten und Quellen werden analysiert...",
            "Writer: Artikel wird verfasst (Durchlauf 1/3)...",
            "Fact-Checker: Behauptungen werden geprüft (Durchlauf 1/3)...",
            "Evaluator: Artikel wird bewertet (Durchlauf 1/3)...",
            "Writer: Artikel wird überarbeitet (Durchlauf 2/3)...",
            "Fact-Checker: Behauptungen werden geprüft (Durchlauf 2/3)...",
            "Evaluator: Artikel wird bewertet (Durchlauf 2/3)...",
            "Writer: Artikel wird überarbeitet (Durchlauf 3/3)...",
            "Fact-Checker: Behauptungen werden geprüft (Durchlauf 3/3)...",
            "Evaluator: Artikel wird bewertet (Durchlauf 3/3)...",
            "Fertig!",
        ]

        content_status_placeholder = st.empty()
        content_progress = st.progress(0)
        content_step_index = [0]

        def on_content_status(msg: str):
            content_status_placeholder.info(f"⏳ {msg}")
            # Advance progress linearly through known steps
            try:
                idx = content_steps.index(msg)
            except ValueError:
                idx = content_step_index[0] + 1
            content_step_index[0] = idx
            content_progress.progress(min(idx / (len(content_steps) - 1), 1.0))

        content_result = content_pipeline.run(
            idea=selected_idea,
            rss_articles=rss_articles,
            gsc_queries=gsc_queries,
            status_callback=on_content_status,
            target_words=st.session_state.get("target_words", 1200),
        )
        st.session_state.content_result = content_result

        content_status_placeholder.empty()
        content_progress.empty()

    # ── Display Article ────────────────────────────────────────────────────────
    content_result = st.session_state.content_result

    if content_result is not None:
        # Errors
        if content_result.errors:
            with st.expander("⚠️ Warnungen / Fehler (Artikel)", expanded=True):
                for err in content_result.errors:
                    st.warning(err)

        # Evaluation scores
        evaluation = content_result.evaluation
        if evaluation:
            scores = evaluation.get("scores", {})
            overall = evaluation.get("overall", 0)
            passed = evaluation.get("passed", False)

            st.markdown("#### Qualitätsbewertung")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Authentizität", f"{scores.get('authentizitaet', 0)}/100")
            m2.metric("Tiefe", f"{scores.get('tiefe', 0)}/100")
            m3.metric("Klarheit", f"{scores.get('klarheit', 0)}/100")
            m4.metric("Relevanz", f"{scores.get('relevanz', 0)}/100")
            m5.metric(
                "Gesamt",
                f"{overall}/100",
                delta="✅ Bestanden" if passed else "❌ Nicht bestanden",
                delta_color="normal" if passed else "inverse",
            )

            revision_label = (
                "Kein Überarbeitungsdurchlauf"
                if content_result.revision_count == 0
                else f"{content_result.revision_count} Überarbeitungsdurchlauf/-läufe"
            )
            st.caption(revision_label)

        # Article content
        article = content_result.article
        if article:
            with st.container(border=True):
                st.title(article.get("title", ""))

                lead = article.get("lead", "")
                if lead:
                    st.markdown(f"_{lead}_")
                    st.divider()

                for section in article.get("sections", []):
                    heading = section.get("heading", "")
                    content = section.get("content", "")
                    if heading:
                        st.subheader(heading)
                    if content:
                        st.markdown(content)

                meta_desc = article.get("meta_description", "")
                if meta_desc:
                    st.caption(f"**Meta-Beschreibung:** {meta_desc}")

        # Social Media Snippets
        _social = getattr(content_result, "social_snippets", {})
        if _social:
            with st.expander("📱 Social Media Snippets", expanded=False):
                _tab_li, _tab_x, _tab_nl = st.tabs(["LinkedIn", "X / Twitter", "Newsletter-Teaser"])
                with _tab_li:
                    st.text_area(
                        "LinkedIn",
                        value=_social.get("linkedin", ""),
                        height=200,
                        label_visibility="collapsed",
                    )
                with _tab_x:
                    _tw = _social.get("twitter", "")
                    st.text_area(
                        "X/Twitter",
                        value=_tw,
                        height=100,
                        label_visibility="collapsed",
                    )
                    st.caption(f"{len(_tw)}/280 Zeichen")
                with _tab_nl:
                    st.text_area(
                        "Newsletter-Teaser",
                        value=_social.get("newsletter_teaser", ""),
                        height=100,
                        label_visibility="collapsed",
                    )

        # Agent detail outputs for article pipeline
        if show_details:
            st.divider()
            st.subheader("🔍 Agent-Outputs (Artikel-Pipeline)")

            with st.expander("Research Notes", expanded=False):
                st.markdown(content_result.research_notes or "_Keine Daten_")

            if evaluation and evaluation.get("feedback"):
                with st.expander("Evaluator-Feedback", expanded=False):
                    st.markdown(evaluation.get("feedback", "_Kein Feedback_"))

else:
    pass
