from typing import List

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


def find_position(table: List[List[str]], user: str, term: str) -> (int, int):
    """
    returns the tuple (updated operation list, original history, new history)
    """
    # find the header row and column
    rows = table  # just an alias
    cols = list(map(list, zip(*rows)))
    users = next(col for col in cols if 'なまえ' in col)  # don't work if there exist the user with the name 'なまえ'
    terms = next(row for row in rows if '月AM' in row)  # same as above

    # find target indices of update
    if user not in users:
        raise ValueError('ユーザー {} が見つかりません'.format(user))
    row_id = users.index(user)
    if term not in terms:
        raise ValueError('期間 {} が見つかりません'.format(term))
    column_id = terms.index(term)

    return row_id, column_id


def get_sheet(worksheet: str, sheetindex: int, credential: str) -> gspread.Worksheet:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential, scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_key(worksheet)
    worksheets = wks.worksheets()
    return worksheets[sheetindex]


def users(table: List[List[str]]) -> List[str]:
    """
    find user list from table
    """
    if not table:
        raise AssertionError("call fetch_table method before")
    cols = list(map(list, zip(*table)))
    # don't work unless the header string is 'なまえ', and there is no user with name 'なまえ.'
    user_column_identifier = 'なまえ'
    users_column = next(col for col in cols if user_column_identifier in col)
    idx = users_column.index(user_column_identifier)
    return users_column[idx + 1:]


def terms(table: List[List[str]]) -> List[str]:
    """
    find term list from table
    """
    if not table:
        raise AssertionError("call fetch_table method before")
    # see the comment of users
    terms_row_identifier = '買値'
    terms_row = next(row for row in table if terms_row_identifier in row)
    idx = terms_row.index(terms_row_identifier)
    return terms_row[idx:idx + 13]
