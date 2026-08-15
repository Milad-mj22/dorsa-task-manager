import os
import json
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

class GoogleSheetsManager:
    """مدیریت اتصال و عملیات روی Google Sheets"""
    
    def __init__(self):
        # مسیر فایل credentials
        self.credentials_path = os.path.join(settings.BASE_DIR, 'credentials', 'pars-python-e4a88a344a86.json')
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.sheet_id = settings.GOOGLE_SHEET_ID  # از settings بگیرید
        
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
            return None
    
    def get_sheet_data(self, range_name='Sheet1!A:Z'):
        """دریافت داده‌ها از Google Sheets"""
        try:
            credentials = self.get_credentials()
            if not credentials:
                return None
                
            service = build('sheets', 'v4', credentials=credentials)
            sheet = service.spreadsheets()
            
            result = sheet.values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
                
            # تبدیل به DataFrame
            headers = values[0]
            data = values[1:]
            df = pd.DataFrame(data, columns=headers)
            
            return df
        except Exception as e:
            print(f"Error fetching sheet data: {e}")
            return None
    
    def get_sheet_data_by_range(self, start_row=2, end_row=None, start_col='A', end_col='Z'):
        """دریافت داده‌ها از محدوده مشخص"""
        range_name = f"Sheet1!{start_col}{start_row}:{end_col}{end_row if end_row else ''}"
        return self.get_sheet_data(range_name)
    
    def get_sheet_metadata(self):
        """دریافت اطلاعات متادیتای شیت"""
        try:
            credentials = self.get_credentials()
            if not credentials:
                return None
                
            service = build('sheets', 'v4', credentials=credentials)
            sheet = service.spreadsheets()
            
            result = sheet.get(spreadsheetId=self.sheet_id).execute()
            return result
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return None