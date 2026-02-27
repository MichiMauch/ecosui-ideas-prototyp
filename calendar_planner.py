"""Content Calendar Planner.

Assigns publish dates to ideas based on urgency (score + trending signals).
Returns a 4-week editorial calendar starting from next Monday.
"""

from __future__ import annotations

from datetime import date, timedelta


def _next_monday(from_date: date | None = None) -> date:
    """Return the next Monday from the given date (or today)."""
    d = from_date or date.today()
    days_until_monday = (7 - d.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # always go to *next* Monday, not today
    return d + timedelta(days=days_until_monday)


def _is_trending(idea: dict, trends_data: list[dict]) -> bool:
    """Return True if the idea title or signals match a trending keyword."""
    title = idea.get("title", "").lower()
    signals_str = str(idea.get("signals", {})).lower()
    for t in trends_data:
        kw = t.get("keyword", "").lower()
        if kw and (kw in title or kw in signals_str):
            return True
    return False


def _has_strong_rss(idea: dict) -> bool:
    """Return True if the idea has a meaningful RSS signal."""
    rss = idea.get("signals", {}).get("rss", "")
    return bool(rss and len(str(rss)) > 20)


def _urgency(idea: dict, trends_data: list[dict]) -> int:
    """
    Assign urgency 1–4:
    1 (Week 1): Score A + (trending OR strong RSS)
    2 (Week 2): Score A without trending
    3 (Week 3): Score B
    4 (Week 4): Score C or unknown
    """
    score = idea.get("score", "C")
    trending = _is_trending(idea, trends_data)
    strong_rss = _has_strong_rss(idea)

    if score == "A" and (trending or strong_rss):
        return 1
    if score == "A":
        return 2
    if score == "B":
        return 3
    return 4


_URGENCY_LABELS = {
    1: "Sofort",
    2: "Bald",
    3: "Geplant",
    4: "Rücklog",
}

# Publish slots per week: Mon, Wed, Fri (offsets 0, 2, 4)
_WEEK_SLOTS = [0, 2, 4]


def generate_content_calendar(
    ideas: list[dict],
    trends_data: list[dict],
) -> list[dict]:
    """
    Assign publish dates to ideas based on urgency.

    Returns list of dicts:
      {
        idea: dict,
        publish_date: date,
        week: int (1-4),
        urgency: int (1-4),
        urgency_label: str,
      }
    """
    if not ideas:
        return []

    monday = _next_monday()

    # Sort ideas by urgency (ascending = most urgent first)
    sorted_ideas = sorted(ideas, key=lambda i: _urgency(i, trends_data))

    # Track slot usage per week (3 slots: Mon, Wed, Fri)
    week_slot_counters: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}

    # Phase 1: Initial assignment by urgency (with overflow to next week)
    calendar: list[dict] = []
    for idea in sorted_ideas:
        urg = _urgency(idea, trends_data)
        week = urg  # urgency maps directly to week number

        # If this week is full, spill to next
        while week <= 4 and week_slot_counters[week] >= len(_WEEK_SLOTS):
            week += 1
        if week > 4:
            week = 4  # cap at week 4

        week_slot_counters[week] += 1

        calendar.append({
            "idea": idea,
            "publish_date": monday,  # placeholder, recalculated in Phase 3
            "week": week,
            "urgency": urg,
            "urgency_label": _URGENCY_LABELS.get(urg, "Geplant"),
        })

    # Phase 2: Redistribute — move lowest-priority idea from full weeks into empty next weeks
    changed = True
    while changed:
        changed = False
        for src in [1, 2, 3]:
            dst = src + 1
            src_items = [e for e in calendar if e["week"] == src]
            dst_items = [e for e in calendar if e["week"] == dst]
            if len(src_items) >= 2 and len(dst_items) == 0:
                # Move the last (lowest-priority) idea of src week to dst week
                src_items[-1]["week"] = dst
                changed = True
                break  # restart to handle cascades correctly

    # Phase 3: Recalculate publish dates after redistribution
    calendar.sort(key=lambda e: (e["week"], e["urgency"]))
    week_counters: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
    for entry in calendar:
        w = entry["week"]
        slot_idx = min(week_counters[w], len(_WEEK_SLOTS) - 1)
        week_monday = monday + timedelta(weeks=w - 1)
        entry["publish_date"] = week_monday + timedelta(days=_WEEK_SLOTS[slot_idx])
        week_counters[w] += 1

    return calendar


def week_date_range_label(week_num: int, start_monday: date | None = None) -> str:
    """Return a human-readable label like '03.03-07.03' for a given week."""
    monday = start_monday or _next_monday()
    week_monday = monday + timedelta(weeks=week_num - 1)
    week_friday = week_monday + timedelta(days=4)
    return f"{week_monday.strftime('%d.%m')}-{week_friday.strftime('%d.%m')}"
