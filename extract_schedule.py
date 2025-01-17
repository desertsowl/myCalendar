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

def measure_time(func):
    """関数の実行時間を計測するデコレータ"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[処理時間] {func.__name__}: {end - start:.2f}秒")
        return result
    return wrapper

@measure_time
def fetch_schedule(force_refresh=False):
    """スケジュールページを取得しキャッシュ"""
    cache_file = os.path.join(CACHE_DIR, "schedule_current.html")
    start_time = time.time()  # 処理時間の計測開始
    
    try:
        # force_refreshがTrueの場合は必ず再取得
        if force_refresh:
            print("強制更新モードでスケジュールを取得します")
        elif os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file) < 3600):
            print("有効なキャッシュを使用します")
            with open(cache_file, "r", encoding="utf-8") as f:
                return {
                    'content': f.read(),
                    'processing_time': time.time() - start_time
                }
        
        # Seleniumの処理開始時間
        selenium_start = time.time()
        
        # Seleniumの設定
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        
        # ログインページにアクセス
        login_start = time.time()
        driver.get(LOGIN_URL)
        time.sleep(2)

        # ユーザー名とパスワードを入力
        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "password").submit()
        print(f"[処理時間] ログイン処理: {time.time() - login_start:.2f}秒")

        time.sleep(3)  # ログイン完了を待つ

        # スケジュールページにアクセス
        schedule_start = time.time()
        target_date = datetime.now()
        schedule_url = f"{CYBOZU_URL}?page=ScheduleUserMonth#date=da.{target_date.year}.{target_date.month:02d}.01"
        driver.get(schedule_url)
        time.sleep(3)
        print(f"[処理時間] スケジュールページ取得: {time.time() - schedule_start:.2f}秒")

        # ページソースを取得
        html_content = driver.page_source
        
        if not html_content:
            raise Exception("ページの内容が空です")

        # キャッシュに保存
        cache_start = time.time()
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[処理時間] キャッシュ保存: {time.time() - cache_start:.2f}秒")
        print(f"[処理時間] Selenium全体: {time.time() - selenium_start:.2f}秒")

        return {
            'content': html_content,
            'processing_time': time.time() - start_time
        }

    except Exception as e:
        print(f"スケジュール取得エラー: {str(e)}")
        if os.path.exists(cache_file):
            print("エラーが発生したため、古いキャッシュを使用します")
            with open(cache_file, "r", encoding="utf-8") as f:
                return {
                    'content': f.read(),
                    'processing_time': time.time() - start_time
                }
        return None

    finally:
        try:
            driver.quit()
        except Exception as e:
            print(f"ドライバー終了エラー: {str(e)}")

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
    
    # データの内容をコンソールに表示
    print("\n=== スケジュールデータ ===")
    print(f"抽出されたレコード数: {len(schedule_data)}")
    print("\n最初の5件:")
    for i, item in enumerate(schedule_data[:5], 1):
        print(f"\n{i}件目:")
        print(f"  日付: {item['date']}")
        print(f"  時刻: {item['time']}")
        print(f"  タイトル: {item['title']}")
    
    return schedule_data

