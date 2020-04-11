import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GspreadService:
    def __init__(self, sheetkey: str, sheetindex: int, credential: str):
        self.sheet = get_sheet(sheetkey, sheetindex, credential)
        self.table = None

    def set(self, row, column, value):
        return self.sheet.update_cell(row, column, value)

    def fetch_table(self):
        self.table = self.sheet.get_all_values()


def get_sheet(worksheet: str, sheetindex: int, credential: str) -> gspread.Worksheet:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential, scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(worksheet)
    worksheets = wks.worksheets()
    return worksheets[sheetindex]
