"""
Google Search Console (GSC) data fetcher.

Returns top queries by impressions and CTR for the last N days.
Uses a Service Account for authentication.
"""

import json
import os
from datetime import date, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account


def _parse_creds_json(s: str) -> dict:
    """Parse credentials JSON, auch wenn literale Newlines in String-Values stecken."""
    in_string = False
    escaped = False
    out = []
    for c in s:
        if escaped:
            out.append(c); escaped = False
        elif c == "\\" and in_string:
            out.append(c); escaped = True
        elif c == '"':
            in_string = not in_string; out.append(c)
        elif c == "\n" and in_string:
            out.append("\\n")
        elif c == "\r" and in_string:
            out.append("\\r")
        else:
            out.append(c)
    return json.loads("".join(out))


def _get_service(credentials_file: str):
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    # Fallback: GOOGLE_CREDENTIALS_FILE enthält direkt JSON-Inhalt (z.B. Streamlit Cloud)
    if not creds_json and credentials_file.strip().startswith("{"):
        creds_json = credentials_file
    if creds_json:
        credentials = service_account.Credentials.from_service_account_info(
            _parse_creds_json(creds_json),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
    return build("webmasters", "v3", credentials=credentials)


def fetch_top_queries(
    site_url: str,
    credentials_file: str,
    days_back: int = 7,
    limit: int = 25,
) -> list[dict]:
    """
    Fetch top search queries by impressions for the last `days_back` days.

    Returns a list of dicts with keys:
        query, impressions, clicks, ctr, position
    """
    service = _get_service(credentials_file)

    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days_back)).isoformat()

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}],
    }

    response = (
        service.searchanalytics()
        .query(siteUrl=site_url, body=body)
        .execute()
    )

    results = []
    for row in response.get("rows", []):
        results.append(
            {
                "query": row["keys"][0],
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "ctr": round(row["ctr"] * 100, 2),
                "position": round(row["position"], 1),
            }
        )

    return results


def fetch_top_pages_by_position(
    site_url: str,
    credentials_file: str,
    days_back: int = 7,
    limit: int = 25,
    min_position: float = 1.0,
    max_position: float = 20.0,
) -> list[dict]:
    """
    Fetch top pages by average position for the last `days_back` days.

    Pages on positions 4–15 ("Fast-Ranker") are prime candidates for
    content updates that could push them to the top 3.

    Returns a list of dicts with keys:
        page, impressions, clicks, ctr, position
    """
    service = _get_service(credentials_file)

    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days_back)).isoformat()

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": limit,
        "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}],
    }

    response = (
        service.searchanalytics()
        .query(siteUrl=site_url, body=body)
        .execute()
    )

    results = []
    for row in response.get("rows", []):
        position = round(row["position"], 1)
        if min_position <= position <= max_position:
            results.append(
                {
                    "page": row["keys"][0],
                    "impressions": row["impressions"],
                    "clicks": row["clicks"],
                    "ctr": round(row["ctr"] * 100, 2),
                    "position": position,
                }
            )

    # Sort by position ascending so fast-rankers come first
    results.sort(key=lambda r: r["position"])
    return results
