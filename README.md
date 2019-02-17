# tepco-watt-stats

くらしTEPCO(https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/home/index.page )のページから、電力使用量のデータを取得して、閾値を超えていた場合にSlackに使用量アラートを投げるスクリプトです.

## Usage

### 環境変数の設定

あらかじめ、ログイン用ユーザID、パスワード、Slack Web hookの値を、それぞれ環境変数 TEPCO_WATT_USERNAME と TEPCO_WATT_PASSWORD と SLACK_WEBHOOK_URL にセットしておいてください.

```
export TEPCO_WATT_USERNAME=YOUER_ID
export TEPCO_WATT_PASSWORD=YOUR_PASSWORD
export SLACK_WEBHOOK_URL=YOUR_SLACK_WEBHOOK
```

### 実行
```
# 15時から23時の毎正時に電力使用量のデータをチェックする.
python3 tepco-watt-stats.py

# 15時から21時の間の **:15 と **:45 に電力使用量のデータをチェックする.
python3 tepco-watt-stats.py -e 21 -m 15 -m 45
```