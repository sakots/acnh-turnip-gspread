import datetime
import itertools
from unittest import TestCase
from unittest.mock import Mock

import jaconv

import parse
import parse_result


class TestParseService(TestCase):
    def test_normalize(self):
        self.assertEqual(parse.normalize("＋１００"), "+100")
        self.assertEqual(parse.normalize("ＡＢＣ"), "abc")

    def test_recognize_from_bot(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        message = make_mention("+100")
        message.author = botuser
        result = service.recognize(message)
        self.assertTrue(isinstance(result, parse_result.IgnorableRequest))

    def test_recognize_not_mention(self):
        botuser = bot()
        service = parse.ParseService(botuser)
        message = make_mention("+100")
        service.recognize(message)
        message.mentions = []
        result = service.recognize(message)
        self.assertTrue(isinstance(result, parse_result.IgnorableRequest))

    def test_recognize_empty(self):
        service = parse.ParseService(bot())
        self.assertEqual(service.recognize(make_mention("")), parse_result.EmptyRequest())
        self.assertEqual(service.recognize(make_mention(" ")), parse_result.EmptyRequest())
        self.assertEqual(service.recognize(make_mention("　")), parse_result.EmptyRequest())

    def test_recognize_update(self):
        service = parse.ParseService(bot())

        base = ["月曜午前", "月AM", "午前月曜", "AM月", "AM月　　"]
        small = map(lambda x: x.lower(), base)
        ja = map(lambda x: jaconv.h2z(x, kana=False, digit=True, ascii=True), base)
        term = list(itertools.chain(base, small, ja))
        pat = ["+100 {}", "＋１００ {}", "+{} 100", "100 {}", "１００ {}"]
        ok_cases = [c.format(d) for c in pat for d in term]

        for c in ok_cases:
            message = make_mention(c)
            expected = parse_result.UpdateRequest("月AM", 100)
            self.assertEqual(service.recognize(message), expected)

    def test_recognize_hist(self):
        service = parse.ParseService(bot())
        self.assertEqual(service.recognize(make_mention("hist")), parse_result.HistoryRequest())
        self.assertEqual(service.recognize(make_mention("history")), parse_result.HistoryRequest())

    def test_recognize_bind(self):
        service = parse.ParseService(bot())
        self.assertEqual(
            parse_result.BindRequest("alice"), service.recognize(make_mention("im　alice"))
        )
        self.assertEqual(
            parse_result.BindRequest("ありす"), service.recognize(make_mention("im　ありす"))
        )
        self.assertEqual(
            parse_result.BindRequest("ー"), service.recognize(make_mention("imー"))
        )
        self.assertEqual(
            parse_result.BindRequest("ー"), service.recognize(make_mention("im ー"))
        )
        self.assertEqual(
            parse_result.BindRequest("🍎"), service.recognize(make_mention("im🍎"))
        )

    def test_recognize_who(self):
        service = parse.ParseService(bot())
        self.assertEqual(
            parse_result.WhoAmIRequest(), service.recognize(make_mention("who"))
        )

    def test_recognize_echo(self):
        service = parse.ParseService(bot())
        self.assertEqual(
            parse_result.EchoRequest("echo"), service.recognize(make_mention("echo"))
        )

    def test_recognize_unknown(self):
        service = parse.ParseService(bot())
        self.assertEqual(
            parse_result.UnknownRequest(), service.recognize(make_mention("excellent"))
        )

    def test_parse_update_command(self):
        #       April 2020
        #  Su Mo Tu We Th Fr Sa
        #            1  2  3  4
        #   5  6  7  8  9 10 11
        #  12 13 14 15 16 17 18
        #  19 20 21 22 23 24 25
        #  26 27 28 29 30
        testcases = [
            (
                "水am 100",
                datetime.datetime(2020, 4, 15, 11, 0, 0),
                parse_result.UpdateRequest("水AM", 100),
                "水曜午前",
            ),            (
                "水am",
                datetime.datetime(2020, 4, 15, 11, 0, 0),
                parse_result.InvalidUpdateRequest(),
                "価格が空",
            ),
            (
                "100 水pm",
                datetime.datetime(2020, 4, 15, 12, 0, 0),
                parse_result.UpdateRequest("水PM", 100),
                "水曜午後",
            ),
            (
                "100 水pm",
                datetime.datetime(2020, 4, 16, 12, 0, 0),
                parse_result.UpdateRequest("水PM", 100),
                "水PMが優先される",
            ),
            (
                "100",
                datetime.datetime(2020, 4, 15, 4, 0, 0),
                parse_result.UpdateRequest("火PM", 100),
                "水曜早朝",
            ),
            (
                "100",
                datetime.datetime(2020, 4, 15, 5, 0, 0),
                parse_result.UpdateRequest("水AM", 100),
                "水曜午前",
            ),
            (
                "100",
                datetime.datetime(2020, 4, 12, 4, 0, 0),
                parse_result.UpdateRequest("土PM", 100),
                "日曜早朝",
            ),
            (
                "100",
                datetime.datetime(2020, 4, 12, 5, 0, 0),
                parse_result.UpdateRequest("買値", 100),
                "日曜午前",
            ),
            (
                "100",
                datetime.datetime(2020, 4, 13, 4, 0, 0),
                parse_result.UpdateRequest("買値", 100),
                "月曜早朝",
            ),
            (
                "買い 100",
                datetime.datetime(2020, 4, 13, 4, 0, 0),
                parse_result.UpdateRequest("買値", 100),
                "月曜早朝",
            ),
            (
                "月曜 100",
                datetime.datetime(2020, 4, 13, 9, 0, 0),
                parse_result.InvalidUpdateRequest(),
                "曜日しかない",
            ),
            (
                "am 100",
                datetime.datetime(2020, 4, 13, 9, 0, 0),
                parse_result.InvalidUpdateRequest(),
                "AMしかない",
            ),
        ]
        for command, current, expected, message in testcases:
            result = parse.parse_update_command(command, current)
            self.assertEqual(expected, result, message)


def bot():
    bot = Mock()
    bot.id = 1234
    bot.mention = "<@!1234>"
    return bot


def make_mention(content: str):
    """
    content を bot にメンションするメッセージを返す
    """
    message = Mock()
    message.author.bot = False
    message.content = "<@!{}> {}".format(bot().id, content)
    message.created_at = datetime.datetime(2020, 4, 6, 11, 30, 0)
    message.mentions = [bot()]
    return message
