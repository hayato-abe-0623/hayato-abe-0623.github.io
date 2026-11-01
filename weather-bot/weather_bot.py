"""天気予報を整形し、明示的な --send 指定時だけLINEに送信する。"""
import argparse
import json
import math
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

WEATHER = {
    0: '快晴', 1: 'おおむね晴れ', 2: '一部曇り', 3: '曇り',
    45: '霧', 48: '着氷性の霧', 51: '弱い霧雨', 53: '霧雨', 55: '強い霧雨',
    56: '弱い着氷性の霧雨', 57: '強い着氷性の霧雨',
    61: '弱い雨', 63: '雨', 65: '強い雨', 66: '弱い着氷性の雨', 67: '強い着氷性の雨',
    71: '弱い雪', 73: '雪', 75: '強い雪', 77: '霧雪',
    80: '弱いにわか雨', 81: 'にわか雨', 82: '激しいにわか雨',
    85: '弱いにわか雪', 86: '強いにわか雪', 95: '雷雨',
    96: 'ひょうを伴う雷雨', 99: '激しいひょうを伴う雷雨',
}


def request_json(request, service):
    """HTTPエラーの本文や認証情報はログに出さない。自動再送はしない。"""
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f'{service}: HTTP {exc.code}。設定や利用上限を確認してください。') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError(f'{service}: 通信に失敗しました。送信時は到達状況を確認してから再実行してください。') from None
    except (ValueError, UnicodeError):
        raise RuntimeError(f'{service}: 応答が正しいJSONではありません。') from None


def fetch_weather(latitude, longitude):
    if not (math.isfinite(latitude) and -90 <= latitude <= 90
            and math.isfinite(longitude) and -180 <= longitude <= 180):
        raise ValueError('緯度は-90〜90、経度は-180〜180で指定してください。')
    params = urlencode({
        'latitude': latitude, 'longitude': longitude,
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        'timezone': 'Asia/Tokyo', 'forecast_days': 1,
        'temperature_unit': 'celsius',
    })
    return request_json(Request('https://api.open-meteo.com/v1/forecast?' + params), '天気API')


def format_message(data, city):
    if not city.strip() or len(city) > 80 or '\n' in city or '\r' in city:
        raise ValueError('地域名は1〜80文字の1行で指定してください。')
    try:
        daily = data['daily']
        date = daily['time'][0]
        code = daily['weather_code'][0]
        high = daily['temperature_2m_max'][0]
        low = daily['temperature_2m_min'][0]
        rain = daily['precipitation_probability_max'][0]
        if not isinstance(date, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            raise ValueError
        if code is not None and (type(code) is not int):
            raise ValueError
        for value in (high, low, rain):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError
        if rain is not None and not 0 <= rain <= 100:
            raise ValueError
    except (KeyError, IndexError, TypeError, ValueError):
        raise ValueError('天気データの形式が不正です。送信を中止しました。') from None
    def display(value, unit):
        return '取得できませんでした' if value is None else f'{value:g}{unit}'
    condition = WEATHER.get(code, '不明')
    return (f'{city}の天気予報（{date}・日本時間）\n'
            f'天気：{condition}\n最高：{display(high, "℃")} / 最低：{display(low, "℃")}\n'
            f'降水確率（日内最大）：{display(rain, "%")}\n'
            '出典：Open-Meteo（予報は変わる場合があります）\nhttps://open-meteo.com/')


def credentials():
    token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
    user_id = os.environ.get('LINE_USER_ID', '').strip()
    if not token or '\n' in token or '\r' in token:
        raise ValueError('LINE_CHANNEL_ACCESS_TOKENを環境変数に設定してください。')
    if not re.fullmatch(r'U[0-9a-fA-F]{32}', user_id):
        raise ValueError('LINE_USER_IDに、Uから始まる33文字のユーザーIDを設定してください。')
    return token, user_id


def send_line(text, token, user_id):
    payload = {'to': user_id, 'messages': [{'type': 'text', 'text': text}]}
    request = Request('https://api.line.me/v2/bot/message/push',
                      data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                      method='POST')
    request_json(request, 'LINE API')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--city', default='東京', help='表示する地域名。緯度・経度も合わせて変更してください。')
    parser.add_argument('--latitude', type=float, default=35.6812)
    parser.add_argument('--longitude', type=float, default=139.7671)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--demo', action='store_true', help='架空データで確認。通信も送信もしません。')
    mode.add_argument('--send', action='store_true', help='実際の予報を取得してLINEへ1回送信します。')
    args = parser.parse_args()
    try:
        auth = credentials() if args.send else None
        if args.demo:
            data = {'daily': {'time': ['2026-01-01'], 'weather_code': [2],
                    'temperature_2m_max': [12.5], 'temperature_2m_min': [4.0],
                    'precipitation_probability_max': [30]}}
        else:
            data = fetch_weather(args.latitude, args.longitude)
        message = format_message(data, args.city)
        if args.send:
            send_line(message, *auth)
            print('LINE APIが送信要求を受け付けました。実際の受信はLINEで確認してください。')
        else:
            print('[架空データのデモ・未送信]' if args.demo else '[実際の予報・未送信]')
            print(message)
        return 0
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
