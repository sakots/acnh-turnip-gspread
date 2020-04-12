import csv
from unittest import TestCase

import table
from table import TurnipPriceTableViewService


class TestTurnipPriceTableViewService(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = service()

    def test_find_position(self):
        result = self.service.find_position("charlie", "金PM")
        self.assertEqual(result, table.Found(5, 12))
        result = self.service.find_position("🍎🍒", "月AM")
        self.assertEqual(result, table.Found(8, 3))

    def test_find_terms_row(self):
        result = self.service.find_terms_row()
        self.assertEqual(result, 2)

    def test_find_users_column(self):
        result = self.service.find_users_column()
        self.assertEqual(result, 1)

    def test_find_users(self):
        result = self.service.find_users()
        self.assertEqual(result[:5], ["alice", "bob", "charlie", "dave", "eve"])

    def test_find_terms(self):
        result = self.service.find_terms()
        self.assertEqual(
            result,
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
        )

    def test_find_user_history(self):
        result = self.service.find_user_history("bob")
        self.assertEqual(result, ["109", "94", "89", "121", "207", "495", "167", "111", "76", "95", "63", "45", "81"])

        result = self.service.find_user_history("x")
        self.assertEqual(result, None)

        result = self.service.find_user_history("alice")
        self.assertEqual(result, ["99", "", "64", "", "", "", "", "", "", "", "", "", ""])

def service() -> TurnipPriceTableViewService:
    return TurnipPriceTableViewService(test_table("testdata.tsv"))


def test_table(filename):
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        dat = [row for row in reader]
    return dat
