from flask import Flask, render_template, request
import os
from extract_schedule import fetch_schedule
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

CHROME_DRIVER_PATH = ".venv/driver/chromedriver"
service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service)


def parse_schedule(html):
    """
    HTMLからスケジュールデータを解析して抽出
    日付 > 個人名 > 時間と案件名 の階層構造を返す
    """
    soup = BeautifulSoup(html, "html.parser")
    schedule_data = []

    # 日付ごとのセクションを抽出
    date_sections = soup.find_all("div", class_="date-section")  # 日付を識別するクラス
    for date_section in date_sections:
        date = date_section.find("span", class_="date").text.strip()  # 日付を抽出
        individuals = []

        # 個人名ごとのスケジュールを取得
        person_sections = date_section.find_all("div", class_="person-section")
        for person_section in person_sections:
            person_name = person_section.find("span", class_="person-name").text.strip()  # 個人名を抽出
            events = []

            # 案件ごとの詳細を取得
            event_rows = person_section.find_all("div", class_="event-row")
            for event_row in event_rows:
                time = event_row.find("span", class_="time").text.strip()  # 時間を抽出
                event_name = event_row.find("span", class_="event-name").text.strip()  # 案件名を抽出
                events.append({"time": time, "event_name": event_name})

            individuals.append({"person": person_name, "events": events})

        schedule_data.append({"date": date, "individuals": individuals})

    return schedule_data

@app.route("/")
def index():
    """メインページ"""
    # デフォルトは当月
    month_offset = request.args.get("month_offset", 0, type=int)
    
    # 現在の日付を取得
    today = datetime.now()
    
    # 月のオプション用のデータを作成
    months = []
    for offset in [-1, 0, 1]:
        target_date = today + relativedelta(months=offset)
        months.append({
            'value': offset,
            'label': target_date.strftime('%Y/%m'),
            'selected': offset == month_offset
        })

    # Nameセレクタ用の名前リストを定義
    name_list = ["三島","三輪","伊藤","保田","原田","坂之下","安田","小澤","山口","岡本",
                 "早川","松本","松村","植松","横山","渋谷","百瀬","緒方","菊池","青井","黒田"]

    html = fetch_schedule(month_offset)
    if not html:
        return "スケジュールデータを取得できませんでした。", 500
    schedule_data = parse_schedule(html)
    return render_template("index.html", schedule_data=schedule_data, name_list=name_list, months=months)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
