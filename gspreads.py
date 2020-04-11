from typing import List

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GspreadService:
    def __init__(self, name: str, credential: str):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credential, scope
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(name)
        self.worksheets = spreadsheet.worksheets()

    def update_cell(self, sheet: int, row: int, column: int, value):
        return self.worksheets[sheet].update_cell(row, column, value)

    def get_table(self, sheet: int) -> List[List[str]]:
        return self.worksheets[sheet].get_all_values()
