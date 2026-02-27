"""
Google Trends data fetcher (via pytrends, unofficial API).

Uses interest_over_time for a curated list of Swiss economic keywords.
Returns the top keywords by search interest index (0–100) over the last 7 days.
Returns an empty list on any error so the pipeline continues without Trends data.
"""

from __future__ import annotations

import time


def fetch_trending_topics(geo: str = "CH", limit: int = 20) -> list[dict]:
    """
    Return a list of keywords ranked by current search interest in Switzerland.

    Each item: {"keyword": str, "value": int, "rank": int}
      - value: average trend index (0–100) over last 7 days
      - rank:  1 = highest search interest

    Returns [] on any error (rate-limit, network, missing package, etc.).
    """
    try:
        from pytrends.request import TrendReq
        import config

        keywords = config.TRENDS_KEYWORDS
        pytrends = TrendReq(hl="de-CH", tz=60, timeout=(10, 25))

        # pytrends allows max 5 keywords per request
        batch_size = 5
        scores: dict[str, float] = {}

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i : i + batch_size]
            try:
                pytrends.build_payload(batch, timeframe="now 7-d", geo=geo)
                df = pytrends.interest_over_time()
                if df is not None and not df.empty:
                    for kw in batch:
                        if kw in df.columns:
                            scores[kw] = float(df[kw].mean())
                        else:
                            scores[kw] = 0.0
                else:
                    for kw in batch:
                        scores[kw] = 0.0
            except Exception:
                for kw in batch:
                    scores[kw] = 0.0

            if i + batch_size < len(keywords):
                time.sleep(0.5)

        # Sort by value descending, take top `limit`, assign ranks
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results: list[dict] = []
        for rank, (keyword, value) in enumerate(sorted_items[:limit], start=1):
            results.append({"keyword": keyword, "value": round(value), "rank": rank})

        return results

    except Exception:
        return []
