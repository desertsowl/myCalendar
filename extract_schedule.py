import requests
from bs4 import BeautifulSoup
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service  # Serviceをインポート

# Cybozuログイン情報
CYBOZU_URL = "https://denshin.cybozu.com/o/ag.cgi"
LOGIN_URL = "https://denshin.cybozu.com/login"
USERNAME = "denshin"
PASSWORD = "denshinJ1525"
CHROME_DRIVER_PATH = "/home/user/my_schedule_app/venv/bin/chromedriver"  # ChromeDriverのパスを指定

# キャッシュディレクトリ
CACHE_DIR = "./cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def fetch_schedule(month_offset=0):
    """指定した月のスケジュールページを取得しキャッシュ"""
    cache_file = os.path.join(CACHE_DIR, f"schedule_{month_offset}.html")
    
    # キャッシュが10分以内なら再利用
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file) < 600):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    
    # Seleniumを使用してスケジュールデータを取得
    options = Options()
    options.add_argument("--headless")  # ヘッドレスモードで実行
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(CHROME_DRIVER_PATH)  # Serviceオブジェクトを使用
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

        # スケジュールページに移動
        schedule_url = f"https://denshin.cybozu.com/o/ag.cgi?page=ScheduleIndex&month_offset={month_offset}"
        driver.get(schedule_url)
        time.sleep(3)  # ページロードを待つ

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

