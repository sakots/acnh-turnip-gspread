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
        self.assertEqual(result, ['買値', '月AM', '月PM', '火AM', '火PM', '水AM', '水PM', '木AM', '木PM', '金AM', '金PM', '土AM', '土PM'])


def service() -> TurnipPriceTableViewService:
    return TurnipPriceTableViewService(testdata("testdata.tsv"))


def testdata(filename):
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        table = [row for row in reader]
    return table
