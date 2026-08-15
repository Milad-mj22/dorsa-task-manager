import os
import json
import pandas as pd
import traceback

from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings


class GoogleSheetsManager:
    """مدیریت اتصال و عملیات روی Google Sheets"""

    def __init__(self):
        self.credentials_path = os.path.join(
            settings.BASE_DIR,
            'credentials',
            'pars-python-e4a88a344a86.json'
        )

        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly'
        ]

        self.sheet_id = settings.GOOGLE_SHEET_ID

    def get_credentials(self):
        """دریافت credentials برای اتصال به Google Sheets"""

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.scopes
            )

            return credentials

        except Exception as e:
            print(f"Error loading credentials: {e}")
            traceback.print_exc()
            return None

    def get_service(self):
        """ساخت Google Sheets API service"""

        credentials = self.get_credentials()

        if not credentials:
            return None

        return build(
            'sheets',
            'v4',
            credentials=credentials,
            cache_discovery=False
        )

    def get_sheet_metadata(self):
        """دریافت اطلاعات Spreadsheet"""

        try:
            service = self.get_service()

            if not service:
                return None

            result = service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            return result

        except Exception as e:
            print(f"Error fetching metadata: {e}")
            traceback.print_exc()
            return None

    def get_sheet_names(self):
        """دریافت نام تمام Sheet ها"""

        metadata = self.get_sheet_metadata()

        if not metadata:
            return []

        return [
            sheet['properties']['title']
            for sheet in metadata.get('sheets', [])
        ]

    def get_first_sheet_name(self):
        """دریافت نام اولین Sheet"""

        sheet_names = self.get_sheet_names()

        if not sheet_names:
            return None

        return sheet_names[0]

    def get_sheet_data(self, range_name=None):
        """دریافت داده‌های Google Sheet"""

        try:

            service = self.get_service()

            if not service:
                return None

            # اگر Range مشخص نشده، اولین Sheet را پیدا کن
            if not range_name:

                sheet_name = self.get_first_sheet_name()

                if not sheet_name:
                    print("No sheets found")
                    return None

                range_name = f"'{sheet_name}'!A:Z"

            print(f"Reading range: {range_name}")

            result = service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                print("Google Sheet is empty")
                return pd.DataFrame()

            # اولین ردیف Header
            headers = values[0]

            rows = []

            for row in values[1:]:

                row = list(row)

                # اگر تعداد ستون‌ها کمتر بود
                if len(row) < len(headers):
                    row.extend(
                        [''] * (len(headers) - len(row))
                    )

                # اگر بیشتر بود
                row = row[:len(headers)]

                rows.append(row)

            df = pd.DataFrame(
                rows,
                columns=headers
            )

            return df

        except Exception as e:

            print(f"Error fetching sheet data: {e}")
            traceback.print_exc()

            return None

    def get_sheet_data_by_range(
        self,
        start_row=2,
        end_row=None,
        start_col='A',
        end_col='Z'
    ):
        """دریافت داده‌ها از محدوده مشخص"""

        sheet_name = self.get_first_sheet_name()

        if not sheet_name:
            return None

        if end_row:
            range_name = (
                f"'{sheet_name}'!"
                f"{start_col}{start_row}:"
                f"{end_col}{end_row}"
            )
        else:
            range_name = (
                f"'{sheet_name}'!"
                f"{start_col}{start_row}:"
                f"{end_col}"
            )

        return self.get_sheet_data(range_name)