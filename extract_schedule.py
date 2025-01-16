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
    soup = BeautifulSoup(html, "html.parser")
    schedule_data = []
    
    # HTML構造に応じて解析
    rows = soup.find_all("tr")  # 例: テーブル行を取得
    for row in rows:
        columns = row.find_all("td")
        if columns:
            schedule_data.append([col.text.strip() for col in columns])
    
    return schedule_data

