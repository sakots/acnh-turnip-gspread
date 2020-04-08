import datetime
import itertools
from unittest import TestCase
from unittest.mock import Mock

import jaconv

import chat


class Test(TestCase):
    def test_datetime_to_term(self):
        #       April 2020
        #  Su Mo Tu We Th Fr Sa
        #            1  2  3  4
        #   5  6  7  8  9 10 11 <- use this week
        #  12 13 14 15 16 17 18
        #  19 20 21 22 23 24 25
        #  26 27 28 29 30
        cases = map(lambda d: datetime.datetime(2020, 4, d, 12, 30, 0), range(5, 12))
        expected = ['買値', '月PM', '火PM', '水PM', '木PM', '金PM', '土PM']
        for c, e in zip(cases, expected):
            self.assertEqual(chat.datetime_to_term(c), e)

    def test_read_term(self):
        base = ['月曜午前', '月AM', '午前月曜', 'AM月']
        small = map(lambda x: x.lower(), base)
        ja = map(lambda x: jaconv.h2z(x, ascii=True), base)
        cases = list(itertools.chain(base, small, ja))
        for c in cases:
            self.assertEqual(chat.read_term(c), '月AM')
        self.assertEqual(chat.read_term('買値'), '買値')

        self.assertIsNone(chat.read_term('100'))

    def test_read_price(self):
        cases = ['100', '１００', '１00', '100ベル']
        for c in cases:
            self.assertEqual(chat.read_price(c), 100)

        self.assertIsNone(chat.read_price('月AM'))


class TestChatService(TestCase):
    @staticmethod
    def make_massage(content: str):
        message = Mock()
        message.author.nick = 'alice'
        message.author.bot = False
        message.content = '<!@123> {}'.format(content)
        message.created_at = datetime.datetime(2020, 4, 6, 11, 30, 0)
        return message

    def test_recognize(self):
        service = chat.ChatService("<!@123>", ['alice', 'bob'])

        base = ['月曜午前', '月AM', '午前月曜', 'AM月', 'AM月　　']
        small = map(lambda x: x.lower(), base)
        ja = map(lambda x: jaconv.h2z(x, ascii=True), base)
        term = list(itertools.chain(base, small, ja))
        ok_cases = ['100 {}'.format(c) for c in term] + ['{} 100'.format(c) for c in term]

        for c in ok_cases:
            message = self.make_massage(c)
            expected = chat.UpdateRequest('alice', '月AM', 100)
            self.assertEqual(service.recognize(message), expected)

        bad_cases = ['', '100 100', '月曜AM 月曜AM', 'a b', '100, 月曜AM', '買値 100 100']

        for c in bad_cases:
            with self.assertRaises(ValueError):
                service.recognize(self.make_massage(c))
