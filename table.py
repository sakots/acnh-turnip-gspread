from dataclasses import dataclass
from typing import List, Optional


class FindResult:
    pass


@dataclass
class Found(FindResult):
    # zero-origin index
    user_row: int
    term_column: int


class UserColumnNotFound(FindResult):
    pass


class TermRowNotFound(FindResult):
    pass


class UserNotFound(FindResult):
    pass


class TermNotFound(FindResult):
    pass


class TurnipPriceTableViewService:
    def __init__(self, table: List[List[str]]):
        max_len = max(map(len, table))
        for row in table:
            while len(row) < max_len:
                row.append('')
        self.table = table
        trans = list(map(list, zip(*table)))
        self.trans = trans

    def find_position(self, user: str, term: str) -> FindResult:
        """
        returns the tuple (updated operation list, original history, new history)
        """
        row_id = self.find_terms_row()
        column_id = self.find_users_column()
        if row_id is None:
            return TermRowNotFound()
        if column_id is None:
            return UserColumnNotFound()

        # find the header row and column
        rows = self.table  # just an alias
        columns = list(map(list, zip(*rows)))

        if user not in columns[column_id]:
            return UserNotFound()
        if term not in rows[row_id]:
            return TermNotFound()

        return Found(columns[column_id].index(user), rows[row_id].index(term))

    def find_users_column(self) -> Optional[int]:
        user_column_identifier = "なまえ"
        return next(
            (i for i, col in enumerate(self.trans) if (user_column_identifier in col)),
            None,
        )

    def find_terms_row(self) -> Optional[int]:
        terms_row_identifier = "買値"
        return next(
            (i for i, row in enumerate(self.table) if (terms_row_identifier in row)),
            None,
        )

    def find_users(self) -> Optional[List[str]]:
        head_identifier = "なまえ"
        users_column = self.find_users_column()
        if users_column is None:
            return None
        index = self.trans[users_column].index(head_identifier)
        return self.trans[users_column][index + 1 :]

    def find_terms(self) -> Optional[List[str]]:
        head_identifier = "買値"
        terms_row = self.find_terms_row()
        if terms_row is None:
            return None
        idx = self.table[terms_row].index(head_identifier)
        return self.table[terms_row][idx : idx + 13]
