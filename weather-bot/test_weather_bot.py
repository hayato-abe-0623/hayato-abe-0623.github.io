import copy
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import weather_bot as bot


class WeatherBotTests(unittest.TestCase):
    def setUp(self):
        self.data = {'daily': {'time': ['2026-01-01'], 'weather_code': [61],
            'temperature_2m_max': [12.5], 'temperature_2m_min': [4],
            'precipitation_probability_max': [70]}}

    def test_format_and_attribution(self):
        text = bot.format_message(self.data, '東京')
        for expected in ('弱い雨', '12.5℃', '70%', 'Open-Meteo'):
            self.assertIn(expected, text)

    def test_missing_value_is_not_zero(self):
        self.data['daily']['precipitation_probability_max'] = [None]
        self.assertIn('取得できませんでした', bot.format_message(self.data, '東京'))

    def test_malformed_response(self):
        for data in ({}, {'daily': {}}, None):
            with self.assertRaises(ValueError): bot.format_message(data, '東京')

    def test_bad_coordinates_prevent_network(self):
        with patch.object(bot, 'request_json') as call:
            for lat in (91, float('nan'), float('inf')):
                with self.assertRaises(ValueError): bot.fetch_weather(lat, 140)
            call.assert_not_called()

    def test_demo_never_connects(self):
        with patch('sys.argv', ['bot', '--demo']), patch.object(bot, 'urlopen') as call, patch('builtins.print'):
            self.assertEqual(bot.main(), 0)
            call.assert_not_called()

    def test_send_without_secret_never_connects(self):
        with patch.dict('os.environ', {}, clear=True), patch('sys.argv', ['bot', '--send']), patch.object(bot, 'urlopen') as call, patch('builtins.print'):
            self.assertEqual(bot.main(), 1)
            call.assert_not_called()

    def test_push_payload(self):
        with patch.object(bot, 'request_json', return_value={}) as call:
            bot.send_line('テスト', 'dummy-token', 'U' + 'a' * 32)
            request = call.call_args.args[0]
            self.assertEqual(request.get_method(), 'POST')
            self.assertEqual(bot.json.loads(request.data)['messages'][0]['text'], 'テスト')

    def test_http_error_redacts_body(self):
        error = HTTPError('https://example.invalid', 401, 'secret-token', {}, None)
        with patch.object(bot, 'urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 401') as result:
                bot.request_json(bot.Request('https://example.invalid'), 'LINE API')
            self.assertNotIn('secret-token', str(result.exception))


if __name__ == '__main__':
    unittest.main()
