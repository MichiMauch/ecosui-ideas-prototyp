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


def _get_service(credentials_file: str):
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json),
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
