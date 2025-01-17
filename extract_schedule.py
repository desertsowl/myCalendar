import requests
from bs4 import BeautifulSoup
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service  # Serviceをインポート
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# Cybozuログイン情報
CYBOZU_URL = "https://denshin.cybozu.com/o/ag.cgi"
LOGIN_URL = "https://denshin.cybozu.com/login"
USERNAME = "denshin"
PASSWORD = "denshinJ1525"
CHROME_DRIVER_PATH = ".venv/driver/chromedriver"

# キャッシュディレクトリ
CACHE_DIR = "./cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def fetch_schedule(month_offset=0):
    """指定した月のスケジュールページを取得しキャッシュ"""
    cache_file = os.path.join(CACHE_DIR, f"schedule_{month_offset}.html")
    
    # キャッシュが60分以内なら再利用
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file) < 3600):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    
    # 対象月の日付を計算
    target_date = datetime.now() + relativedelta(months=month_offset)
    schedule_url = f"https://denshin.cybozu.com/o/ag.cgi?page=ScheduleUserMonth#date=da.{target_date.year}.{target_date.month:02d}.01"
    
    # Seleniumの設定
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # ログインページにアクセス
        driver.get(LOGIN_URL)
        time.sleep(2)

        # ユーザー名とパスワードを入力
        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "password").submit()

        time.sleep(3)  # ログイン完了を待つ

        # 修正したURLでスケジュールページにアクセス
        driver.get(schedule_url)
        time.sleep(3)

        # ページソースを取得
        html_content = driver.page_source

        # キャッシュに保存
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content

    finally:
        driver.quit()

def parse_schedule(html):
    """スケジュールHTMLから必要なデータを抽出"""
    # 各行を個別に処理
    schedule_data = []
    
    # 1行ずつ処理
    for line in html.split('\n'):
        # eventLinkで始まる行のみを処理
        if not line.strip().startswith('<div class="eventLink'):
            continue
            
        # 日付の抽出
        date_match = re.search(r'<a class="event"[^>]*Date=da\.([0-9.]+)&', line)
        date = date_match.group(1) if date_match else "日付なし"
            
        # タイトルの抽出
        title_match = re.search(r'<a class="event"[^>]*title="([^"]+)"', line)
        title = title_match.group(1) if title_match else "タイトルなし"
            
        # 時刻の抽出
        if 'allday' in line and 'png' in line:
            time = "終日"
        else:
            # まず<img>タグの後の時刻を探す
            time_match = re.search(r'<img[^>]*>([0-9:-]+)', line)
            if time_match:
                time = time_match.group(1)
            else:
                # <img>タグがない場合は<span class="eventDateTime">の後の時刻を探す
                time_match = re.search(r'<span class="eventDateTime">([0-9:-]+)&nbsp;', line)
                time = time_match.group(1) if time_match else "時刻なし"
        
        schedule_data.append({
            "date": date,
            "time": time,
            "title": title
        })
    
    return schedule_data

