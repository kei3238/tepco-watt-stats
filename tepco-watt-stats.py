#!/usr/bin/env python3

import os
import requests
import csv
import io
import json
import schedule
import time
import click
from datetime import datetime

class TepcoWattStats ():

    def __init__(self, recent_alert_file):

        # ログイン情報設定.
        self.username = os.environ['TEPCO_WATT_USERNAME']
        self.password = os.environ['TEPCO_WATT_PASSWORD']
        self.webhook_url = os.environ['SLACK_WEBHOOK_URL']

        # 前回実行した時の情報を記載したファイル.
        self.recent_alert_file = recent_alert_file

        # スクリプトを実行した年月を取得.
        today = datetime.today()
        self.year = today.year
        self.month = today.month

    def run(self):

        session = requests.Session()

        # ログイン 念のため一度トップページへアクセスして cookie を食べる.
        loginparam = {
            'ACCOUNTUID': self.username,
            'PASSWORD': self.password,
            'HIDEURL': '/pf/ja/pc/mypage/home/index.page?',
            'LOGIN': 'EUAS_LOGIN',
        }
        loginheader = {
            'Referer': 'https://www.kurashi.tepco.co.jp/kpf-login',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        session.get('https://www.kurashi.tepco.co.jp/kpf-login')
        login = session.post(
            'https://www.kurashi.tepco.co.jp/kpf-login', data=loginparam, headers=loginheader,)

        # CSV 取得前に使用量ページの cookie を食べておく必要があるようなのでリクエストを投げる.
        session.get(
            'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page')

        # URL を組み立てて CSV データを取ってくる.
        csv_url = 'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page?ReqID=CsvDL&year=' + \
                str(self.year) + '&month=%00d' % (self.month)

        csvgetheader = {
            'Referer': 'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page',
        }
        csvdata = session.get(csv_url, headers=csvgetheader)
        csvdata.encoding = csvdata.apparent_encoding

        # スクリプトを実行した日の電力使用総量を取得.
        data = csv.reader(io.StringIO(initial_value=csvdata.text))
        data = [data_of_each_day for data_of_each_day in data]
        
        # 現在までの電力使用量を取得 (kWh).
        watt_sum = float(data[-1][8])

        # 取得した電力使用量データの対象日を取得 (YYYY/MM/DD).
        date_of_data = data[-1][4]

        # アラートをSlackに通知
        if watt_sum > 40:
            self.watt_alert(watt_sum, 40, date_of_data)
        elif watt_sum > 35:
            self.watt_alert(watt_sum, 35, date_of_data)
        elif watt_sum > 30:
            self.watt_alert(watt_sum, 30, date_of_data)
        elif watt_sum > 25:
            self.watt_alert(watt_sum, 25, date_of_data)
        elif watt_sum > 20:
            self.watt_alert(watt_sum, 20, date_of_data)
        elif watt_sum > 15:
            self.watt_alert(watt_sum, 15, date_of_data)
        elif watt_sum > 10:
            self.watt_alert(watt_sum, 10, date_of_data)

    # 実行日の電力使用総量が閾値を超えていたらSlackに通知.
    def watt_alert (self, current_watt_sum, threthold, date_of_data):

        new_alert_info = {
            'year': date_of_data.split('/')[0],
            'month': date_of_data.split('/')[1],
            'day': date_of_data.split('/')[2],
            'threshold': threthold
        }

        if os.path.exists(self.recent_alert_file):
            with open(self.recent_alert_file, 'r') as fp:
                recent_alert_info = json.load(fp)
        else:
            recent_alert_info = {}

        # まだ通知していないアラートの場合にSlackに通知.
        if recent_alert_info != new_alert_info:
            alert_text = f'{date_of_data}の電力使用量が{threthold} kWhを超えました. 現在の電力使用量は{current_watt_sum:.1f} kWhです.'
            
            # Slackへのwebhook.
            requests.post(self.webhook_url, data = json.dumps({
                'text': alert_text
            }))

            # コンソールにも出力.
            print ('[INFO] ' + alert_text)
            
            # 最新のアラートの情報を保存.
            with open(self.recent_alert_file, 'w') as fp:
                json.dump(new_alert_info, fp, indent=4)

@click.command()
@click.option('-e', '--end-hour', default='23', help='アラート通知を終了する時刻 (時). デフォルトは23.', type=click.IntRange(16, 24))
@click.option('-m', '--minutes', default='0', help='アラートを通知する毎時の時刻 (分). デフォルトは00.', multiple=True, type=click.IntRange(0, 59))
def cmd(end_hour, minutes):
    # アラートを開始・終了する時間.
    # 現状15時以降しかデータが更新されない仕様なので開始時刻は15時で固定.
    # https://support.tepco.co.jp/faq/show/880?site_domain=kurashi
    alert_start_time = 15  
    alert_end_time = end_hour

    def job():
        proc = TepcoWattStats('./recent_alert.txt')
        proc.run()
    
    # うまく動かない.
    #schedule.every().day.at(":15").do(job)
    #schedule.every().day.at(":30").do(job)

    # アラートを通知する時刻を指定.
    for hour in range(alert_start_time, alert_end_time):
        hour = str(hour).zfill(2)
        for minute in minutes:
            minute = str(minute).zfill(2)
            print ('[INFO] Watt sum will be checked at ' + f'{hour}:{minute}')
            schedule.every().day.at(f'{hour}:{minute}').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
    
if __name__ == '__main__':
    cmd()