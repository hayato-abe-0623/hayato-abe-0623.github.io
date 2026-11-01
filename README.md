# Hayato Portfolio / Python Weather LINE Bot

天気予報を取得してLINEへ通知する、学習用のPython制作物です。
コードの理解・修正・動作検証を進めるための初期版です。

## 構成

- `index.html`：制作物を紹介するポートフォリオ
- `weather-bot/weather_bot.py`：予報取得・日本語整形・LINE送信
- `weather-bot/test_weather_bot.py`：外部通信を使わない自動テスト
- `.gitignore`：認証情報や一時ファイルの除外

## できること

Open-Meteoの当日予報（日本時間）から天気・最高／最低気温・降水確率の日内最大値を取得し、LINE Messaging APIのpush APIで1ユーザーに送ります。
地域名は表示用です。地域を変えるときは緯度・経度も必ず変更します。
欠測は0とせず「取得できませんでした」と表示。不正な応答・通信エラーでは処理を止めます。
Webhookを使う対話Botではなく、実行時に1回通知するプログラムです。

## 最初に試す（認証不要・外部通信なし）

Python 3.10以上を使用してください。追加ライブラリは不要です。
ターミナルで、このREADMEがあるフォルダへ移動して実行します。

```sh
python3 weather-bot/weather_bot.py --demo
```

2026-01-01の架空データが表示されます。現在の予報ではなく、LINEにも送信されません。

## 実際の予報を確認（送信なし）

```sh
python3 weather-bot/weather_bot.py
```

初期値は東京駅付近です。例：気仙沼市中心部付近を指定する場合：

```sh
python3 weather-bot/weather_bot.py --city 気仙沼 --latitude 38.908 --longitude 141.570
```

インターネット接続が必要です。Open-Meteoの利用条件・制限に従ってください。

## LINEに送信するための設定

1. LINE公式アカウントを作成し、LINE Official Account ManagerでMessaging APIを有効にします。
2. LINE Developersコンソールで、そのチャネルのMessaging APIタブからチャネルアクセストークンを発行します。
3. 自分のLINEで公式アカウントを友だち追加します。
4. チャネル基本設定の「あなたのユーザーID」を確認します。表示名や友だち検索用のLINE IDとは異なる、Uから始まる33文字です。表示されない場合はビジネスIDとLINEアカウントの連携を確認してください。
5. 次の環境変数を、自分の端末のターミナルに設定します。トークンをコード・HTML・README・GitHubへ記載しないでください。

macOS標準のzshでは、以下の入力方法ならトークンを画面に表示せず、コマンド履歴にも値を直接書かずに設定できます。

```sh
read -s 'LINE_CHANNEL_ACCESS_TOKEN?チャネルアクセストークン: '
echo
export LINE_CHANNEL_ACCESS_TOKEN
read 'LINE_USER_ID?あなたのユーザーID: '
export LINE_USER_ID
```

同じターミナルで、送信先が自分であることを確認して実行：

```sh
python3 weather-bot/weather_bot.py --city 気仙沼 --latitude 38.908 --longitude 141.570 --send
```

このコマンドはLINEへ実際に送信します。送信回数は公式アカウントのプランや上限の影響を受けます。
HTTP成功は受信の保証ではありません。自分のLINEで受信を確認してください。
タイムアウト時は送信済みの可能性もあるため、受信状況を見てから再実行してください。重複防止のため自動再送は実装していません。
このプログラムは`.env`を自動読込しません。通常実行と`--demo`ではトークンは不要です。

## 検証

```sh
python3 -m unittest discover -s weather-bot -v
```

日本語整形・欠測・不正データ・緯度検証・デモ時の通信禁止・認証未設定時の送信禁止・送信JSON・HTTPエラー表示をテストしています。
実API接続、LINEでの実機受信、定期実行は未検証です。定期実行の仕組みは含めていません。

## GitHubへ載せるファイル

このフォルダの構成を保ってリポジトリへ追加します。秘密情報を入れたファイルはアップロードしないでください。
`index.html`にはコードと手順を内蔵しています。Pythonを実行する場合やテストする場合は、`weather-bot`フォルダも使用してください。
HTMLは紹介ページです。GitHub PagesなどでHTMLを公開してもPythonは実行されません。BotはPythonのある端末やサーバーで実行します。

## 設計を説明するポイント

- `fetch_weather`：HTTP GETで予報を取得
- `format_message`：JSONを検証し、人が読めるメッセージに変換
- `send_line`：認証ヘッダー付きのHTTP POSTで送信
- `main`：引数でデモ・確認・送信を切り替え

## 公式ドキュメント・出典

- [Open-Meteo Forecast API](https://open-meteo.com/en/docs)
- [Open-Meteo利用条件](https://open-meteo.com/en/terms)
- [LINE Messaging APIの開始](https://developers.line.biz/ja/docs/messaging-api/getting-started/)
- [LINEユーザーIDの取得](https://developers.line.biz/ja/docs/messaging-api/getting-user-ids/)
- [LINE Messaging APIリファレンス](https://developers.line.biz/ja/reference/messaging-api/)

天気データの出典はOpen-Meteoです。通知文にも出典リンクを含めています。
