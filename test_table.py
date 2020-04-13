import csv
from unittest import TestCase

import table
from table import TurnipPriceTableViewService


class TestTurnipPriceTableViewService(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("testdata.tsv", mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = [row for row in reader]
        cls.service = TurnipPriceTableViewService(rows)

    def test_find_position(self):
        self.assertEqual(table.Found(5, 12), self.service.find_position("3", "金PM"))
        self.assertEqual(table.Found(8, 3), self.service.find_position("6", "月AM"))

    def test_find_terms_row(self):
        self.assertEqual(2, self.service.find_term_row())

    def test_find_users_column(self):
        self.assertEqual(0, self.service.find_row_id_column())

    def test_find_row_ids(self):
        self.assertEqual(["1", "2", "3", "4", "5", "6"], self.service.find_row_ids())

    def test_find_terms(self):
        self.assertEqual(
            [
                "買値",
                "月AM",
                "月PM",
                "火AM",
                "火PM",
                "水AM",
                "水PM",
                "木AM",
                "木PM",
                "金AM",
                "金PM",
                "土AM",
                "土PM",
            ],
            self.service.find_terms(),
        )

    def test_find_user_history(self):
        self.assertEqual(
            [
                "109",
                "94",
                "89",
                "121",
                "207",
                "495",
                "167",
                "111",
                "76",
                "95",
                "63",
                "45",
                "81",
            ],
            self.service.find_history_by_row_id("2"),
        )

        result = self.service.find_history_by_row_id("100")
        self.assertEqual(None, result)

        result = self.service.find_history_by_row_id("1")
        self.assertEqual(
            result, ["99", "", "64", "", "", "", "", "", "", "", "", "", ""]
        )
