"""SEO Traffic Potential Calculator.

Computes estimated monthly traffic gains from:
- Fast-Rankers: pages ranking pos 4-15 that could jump to pos 3
- CTR-Gap: queries with low CTR relative to position
"""

from __future__ import annotations

CTR_BENCHMARKS = {
    1: 0.278, 2: 0.158, 3: 0.110, 4: 0.079, 5: 0.058,
    6: 0.043, 7: 0.033, 8: 0.026, 9: 0.020, 10: 0.016,
    11: 0.012, 12: 0.010, 15: 0.007, 20: 0.004,
}

MAX_TOTAL_POTENTIAL = 5000  # cap at plausible upper bound


def _get_ctr_for_position(pos: float) -> float:
    """Interpolate CTR for a given position using benchmark table."""
    positions = sorted(CTR_BENCHMARKS.keys())
    if pos <= positions[0]:
        return CTR_BENCHMARKS[positions[0]]
    if pos >= positions[-1]:
        return CTR_BENCHMARKS[positions[-1]]
    # Find surrounding positions for linear interpolation
    lower = max(p for p in positions if p <= pos)
    upper = min(p for p in positions if p >= pos)
    if lower == upper:
        return CTR_BENCHMARKS[lower]
    frac = (pos - lower) / (upper - lower)
    return CTR_BENCHMARKS[lower] + frac * (CTR_BENCHMARKS[upper] - CTR_BENCHMARKS[lower])


def calculate_seo_potential(gsc_pages: list[dict], gsc_queries: list[dict]) -> dict:
    """
    Calculate monthly traffic potential from GSC data.

    Returns:
      {
        "fast_ranker_potential": int,    # monthly clicks if Fast-Rankers reach pos 3
        "ctr_gap_potential": int,        # monthly clicks from underperforming keywords
        "total_potential": int,
        "top_opportunities": list[dict], # top 5 pages/queries with potential & delta
      }
    """
    opportunities: list[dict] = []

    # --- Fast-Rankers: pages pos 4-15 ---
    fast_ranker_total = 0
    for page in gsc_pages:
        pos = float(page.get("position", 0))
        impressions = int(page.get("impressions", 0))
        if not (4 <= pos <= 15) or impressions == 0:
            continue
        ctr_current = _get_ctr_for_position(pos)
        ctr_target = CTR_BENCHMARKS[3]  # target: position 3
        delta_ctr = ctr_target - ctr_current
        if delta_ctr <= 0:
            continue
        # Scale from 7-day impressions to monthly
        monthly_delta = int(impressions * delta_ctr * (30 / 7))
        if monthly_delta <= 0:
            continue
        fast_ranker_total += monthly_delta
        url = page.get("page", "")
        label = url.rstrip("/").split("/")[-1] or url
        label = label[:60] if label else url[:60]
        opportunities.append({
            "type": "fast_ranker",
            "label": label,
            "url": url,
            "current_position": round(pos, 1),
            "target_position": 3,
            "monthly_delta": monthly_delta,
        })

    # --- CTR-Gap: queries pos < 20, CTR < 3% ---
    ctr_gap_total = 0
    for query in gsc_queries:
        pos = float(query.get("position", 0))
        impressions = int(query.get("impressions", 0))
        ctr_pct = float(query.get("ctr", 0))
        ctr_frac = ctr_pct / 100
        if pos >= 20 or impressions == 0 or ctr_pct >= 3.0:
            continue
        ctr_expected = _get_ctr_for_position(pos)
        delta_ctr = ctr_expected - ctr_frac
        if delta_ctr <= 0:
            continue
        monthly_delta = int(impressions * delta_ctr * (30 / 7))
        if monthly_delta <= 0:
            continue
        ctr_gap_total += monthly_delta
        kw = query.get("query", "")
        opportunities.append({
            "type": "ctr_gap",
            "label": kw[:60],
            "keyword": kw,
            "current_position": round(pos, 1),
            "current_ctr_pct": ctr_pct,
            "monthly_delta": monthly_delta,
        })

    # Sort by potential, take top 5
    opportunities.sort(key=lambda x: x["monthly_delta"], reverse=True)
    top_opportunities = opportunities[:5]

    total_potential = min(fast_ranker_total + ctr_gap_total, MAX_TOTAL_POTENTIAL)

    return {
        "fast_ranker_potential": min(fast_ranker_total, MAX_TOTAL_POTENTIAL),
        "ctr_gap_potential": min(ctr_gap_total, MAX_TOTAL_POTENTIAL),
        "total_potential": total_potential,
        "top_opportunities": top_opportunities,
    }
