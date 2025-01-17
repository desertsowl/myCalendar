from flask import Flask, render_template, request
import os
from extract_schedule import fetch_schedule
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

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
    
    # 日付でグループ化
    grouped_schedule = {}
    for item in schedule_data:
        date = item['date']
        if date not in grouped_schedule:
            grouped_schedule[date] = []
        grouped_schedule[date].append({
            'time': item['time'],
            'title': item['title']
        })
    
    return render_template(
        "index.html", 
        schedule_data=grouped_schedule, 
        name_list=name_list, 
        months=months
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
