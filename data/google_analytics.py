"""
Google Analytics 4 (GA4) data fetcher.

Returns top-performing pages and engagement metrics for the last N days.
Uses a Service Account for authentication.
"""

import json
import os
from datetime import date, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account


def _get_client(credentials_file: str) -> BetaAnalyticsDataClient:
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    # Fallback: GOOGLE_CREDENTIALS_FILE enthält direkt JSON-Inhalt (z.B. Streamlit Cloud)
    if not creds_json and credentials_file.strip().startswith("{"):
        creds_json = credentials_file
    if creds_json:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    return BetaAnalyticsDataClient(credentials=credentials)


def fetch_top_pages(
    property_id: str,
    credentials_file: str,
    days_back: int = 7,
    limit: int = 20,
) -> list[dict]:
    """
    Fetch top pages by page views with engagement rate for the last `days_back` days.

    Returns a list of dicts with keys:
        page_title, page_path, page_views, engagement_rate
    """
    client = _get_client(credentials_file)

    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days_back)).isoformat()

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="pageTitle"),
            Dimension(name="pagePath"),
        ],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="engagementRate"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[
            {"metric": {"metric_name": "screenPageViews"}, "desc": True}
        ],
        limit=limit,
    )

    response = client.run_report(request)

    results = []
    for row in response.rows:
        results.append(
            {
                "page_title": row.dimension_values[0].value,
                "page_path": row.dimension_values[1].value,
                "page_views": int(row.metric_values[0].value),
                "engagement_rate": round(float(row.metric_values[1].value) * 100, 1),
            }
        )

    return results
