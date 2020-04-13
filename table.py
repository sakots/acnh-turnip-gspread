import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


class FindResult:
    pass


@dataclass
class Found(FindResult):
    # zero-origin index
    user_row: int
    term_column: int


class IdColumnNotFound(FindResult):
    pass


class TermRowNotFound(FindResult):
    pass


class UserNotFound(FindResult):
    pass


class TermNotFound(FindResult):
    pass


# 一致するセルがある列を行ID列とする
ROW_IDS_COLUMN_IDENTIFIER = "ID"

# 一致するセルがある行を期間行とする
TERMS_ROW_IDENTIFIER = "買値"


class TurnipPriceTableViewService:
    def __init__(self, table: List[List[str]]):
        max_len = max(map(len, table))
        for row in table:
            while len(row) < max_len:
                row.append("")
        self.table = table
        trans = list(map(list, zip(*table)))
        self.trans = trans

    def find_position(self, row_id: str, term: str) -> FindResult:
        """
        行IDと期間から更新すべき場所を探す。
        """
        term_row_index = self.find_term_row()
        id_column_index = self.find_row_id_column()
        if term_row_index is None:
            return TermRowNotFound()
        if id_column_index is None:
            return IdColumnNotFound()

        # find the header row and column
        rows = self.table  # just an alias
        columns = self.trans

        if row_id not in columns[id_column_index]:
            return UserNotFound()
        if term not in rows[term_row_index]:
            return TermNotFound()

        return Found(
            columns[id_column_index].index(row_id), rows[term_row_index].index(term)
        )

    def find_row_id_column(self) -> Optional[int]:
        """
        行IDの列を探す。`ID`というセルを含む列を返す。
        """
        return next(
            (
                i
                for i, col in enumerate(self.trans)
                if (ROW_IDS_COLUMN_IDENTIFIER in col)
            ),
            None,
        )

    def find_term_row(self) -> Optional[int]:
        """
        期間行を探す。`買値`というセルを含む列を返す。
        """
        return next(
            (i for i, row in enumerate(self.table) if (TERMS_ROW_IDENTIFIER in row)),
            None,
        )

    def find_terms(self) -> Optional[List[str]]:
        row, left, right = self.find_terms_range()
        return self.table[row][left:right]

    def find_row_ids(self) -> Optional[List[str]]:
        col, top, bottom = self.find_row_ids_range()
        return self.trans[col][top:bottom]

    def find_terms_range(self) -> Optional[Tuple[int, int, int]]:
        """
        期間を含む行の (列index, 左端列のindex, 右端列のindex+1)を返す。
        "買値" のセルを始点とし、そこから右に連なる13個のセルを返す。
        """
        terms_row = self.find_term_row()
        if terms_row is None:
            return None
        col = self.table[terms_row].index(TERMS_ROW_IDENTIFIER)
        return terms_row, col, col + 13

    def find_row_ids_range(self) -> Optional[Tuple[int, int, int]]:
        """
        行IDを含む列の (列index, 上端行のindex, 下端行のindex+1)を返す。
        "1" のセル始点とし、そこから下に連続する数字のみからなるセルを返す。
        """
        row_ids_column = self.find_row_id_column()
        if row_ids_column is None:
            return None
        top_row = self.trans[row_ids_column].index(ROW_IDS_COLUMN_IDENTIFIER) + 1
        if self.table[top_row][row_ids_column] != "1":
            return None
        bottom_row = top_row
        height = len(self.table)
        while bottom_row < height and re.match(
            r"^[0-9]+$", self.table[bottom_row][row_ids_column]
        ):
            bottom_row += 1
        return row_ids_column, top_row, bottom_row

    def find_history_by_row_id(self, row_id: str) -> Optional[List[str]]:
        """
        row_id で指定したユーザーの履歴を返す。
        """
        row_id_column = self.find_row_id_column()
        if row_id not in self.trans[row_id_column]:
            return None
        # その行は何列目か
        row = self.trans[row_id_column].index(row_id)
        _, left, right = self.find_terms_range()
        return self.table[row][left:right]
