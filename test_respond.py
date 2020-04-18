from unittest import TestCase

from respond import prediction_url, format_history


class Test(TestCase):
    def test_prediction_url(self):
        history = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.assertEqual(
            "https://turnipprophet.io/?prices=1.2.3.4.5.6.7.8.9.10.11.12.13&",
            prediction_url(history),
        )
        history = [1, 2, "", 4, 5, None, 7, 8, 9, 10, 11, 12, 13]
        self.assertEqual(
            "https://turnipprophet.io/?prices=1.2..4.5..7.8.9.10.11.12.13&",
            prediction_url(history),
        )

    def test_format_history(self):
        self.assertEqual(
            "1 2/3 4/5 6/7 8/9 10/11 12/13",
            format_history( ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"])
        )
        self.assertEqual(
            "1 2/3 4/5 6/7 -/9 10/11 12/13",
            format_history(["1", "2", "3", "4", "5", "6", "7", "", "9", "10", "11", "12", "13"])
        )
        self.assertEqual(
            "1 2/3 4/5 6/7 -/9 10/11 12/13",
            format_history(["1", "2", "3", "4", "5", "6", "7", "-", "9", "10", "11", "12", "13"])
        )
        self.assertEqual(
            "1 2/3 4/5 6/7 -/9 10/11",
            format_history( ["1", "2", "3", "4", "5", "6", "7", "-", "9", "10", "11", "-", "-"])
        )
        self.assertEqual(
            "1 2/3 4/5 6/7 -/9 10",
            format_history(["1", "2", "3", "4", "5", "6", "7", "-", "9", "10", "-", "-", "-"])
        )
