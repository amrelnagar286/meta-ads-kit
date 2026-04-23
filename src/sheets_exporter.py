"""
Google Sheets Exporter — View-only Google Sheets integration.
Uses service account JWT authentication to read/write spreadsheets.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)


def _get_sheets_service():
    """Build Google Sheets API service from credentials."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_path = os.getenv(
            "GOOGLE_SHEETS_CREDENTIALS", "config/google_credentials.json"
        )
        if not os.path.exists(creds_path):
            log.warning(f"Google credentials not found at {creds_path}")
            return None

        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        return build("sheets", "v4", credentials=creds)
    except ImportError:
        log.warning("Google API libraries not installed. Run: pip install google-api-python-client google-auth")
        return None
    except Exception as e:
        log.error(f"Failed to init Google Sheets service: {e}")
        return None


def read_sheet(
    spreadsheet_id: str,
    range_name: str = "Sheet1!A:Z",
) -> pd.DataFrame:
    """Read data from a Google Sheet into a DataFrame."""
    service = _get_sheets_service()
    if not service:
        return pd.DataFrame()

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        log.error(f"Failed to read sheet: {e}")
        return pd.DataFrame()


def write_to_sheet(
    spreadsheet_id: str,
    df: pd.DataFrame,
    sheet_name: str = "Sheet1",
    clear_first: bool = True,
) -> bool:
    """Write a DataFrame to a Google Sheet."""
    service = _get_sheets_service()
    if not service:
        return False

    try:
        range_name = f"{sheet_name}!A1"
        values = [df.columns.tolist()] + df.fillna("").values.tolist()
        body = {"values": values}

        if clear_first:
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:Z",
                body={},
            ).execute()

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()
        log.info(f"Wrote {len(df)} rows to {sheet_name}")
        return True
    except Exception as e:
        log.error(f"Failed to write to sheet: {e}")
        return False


def export_dataframe_to_sheets(
    df: pd.DataFrame,
    spreadsheet_id: str,
    sheet_name: str = "MetaAdsData",
) -> bool:
    """High-level export of a DataFrame to Google Sheets."""
    if df.empty:
        log.info("No data to export")
        return False

    return write_to_sheet(
        spreadsheet_id=spreadsheet_id,
        df=df,
        sheet_name=sheet_name,
        clear_first=True,
    )


def create_new_spreadsheet(title: str) -> Optional[str]:
    """Create a new Google Spreadsheet and return its ID."""
    service = _get_sheets_service()
    if not service:
        return None

    try:
        spreadsheet = service.spreadsheets().create(
            body={"properties": {"title": title}},
            fields="spreadsheetId",
        ).execute()
        sid = spreadsheet.get("spreadsheetId")
        log.info(f"Created spreadsheet: {sid}")
        return sid
    except Exception as e:
        log.error(f"Failed to create spreadsheet: {e}")
        return None
