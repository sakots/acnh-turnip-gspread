from unittest import TestCase

import pymongo_inmemory

from bind import BindService


class TestBindService(TestCase):
    def test_bind(self):
        client = pymongo_inmemory.MongoClient()  # No need to provide host
        db = client["testdb"]
        collection = db["users"]

        binds = BindService(collection)

        self.assertEqual(binds.find_row_id(1), None)
        binds.bind(1, 1)
        self.assertEqual(binds.find_row_id(1), 1)
        binds.bind(1, 2)
        self.assertEqual(binds.find_row_id(1), 2)
