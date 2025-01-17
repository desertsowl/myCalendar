from flask import Flask, render_template, request, jsonify
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

def get_name_list():
    """member.txtから名前リストを読み込む"""
    try:
        with open("./member.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Warning: member.txt が見つかりません")
        return []

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

    # member.txtから名前リストを取得
    name_list = get_name_list()

    # 常に今月のデータを取得
    html = fetch_schedule()  # month_offsetは使用しない
    if not html:
        return "スケジュールデータを取得できませんでした。", 500
    
    schedule_data = parse_schedule(html)
    
    # 選択された月のデータのみをフィルタリング
    target_date = today + relativedelta(months=month_offset)
    target_year_month = f"{target_date.year}.{target_date.month:02d}"
    
    filtered_data = [
        item for item in schedule_data
        if item['date'].startswith(target_year_month)
    ]
    
    # 日付でグループ化
    grouped_schedule = {}
    for item in filtered_data:
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

@app.route("/api/schedule")
def get_filtered_schedule():
    """指定された名前と月のスケジュールデータを返すAPI"""
    name = request.args.get("name", "")
    month_offset = request.args.get("month_offset", 0, type=int)
    
    # 今月のデータのみを取得
    html = fetch_schedule()  # month_offsetは使用しない
    if not html:
        return jsonify({"error": "データを取得できませんでした"}), 500
    
    schedule_data = parse_schedule(html)
    
    # 名前でフィルタリング
    if name:
        filtered_data = [
            item for item in schedule_data
            if name in item['title']
        ]
    else:
        filtered_data = schedule_data
    
    # 選択された月のデータのみをフィルタリング
    target_date = datetime.now() + relativedelta(months=month_offset)
    target_year_month = f"{target_date.year}.{target_date.month:02d}"
    
    # 日付の比較を修正
    month_filtered_data = []
    for item in filtered_data:
        try:
            date_parts = item['date'].split('.')
            item_year = int(date_parts[0])
            item_month = int(date_parts[1])
            
            if (item_year == target_date.year and 
                item_month == target_date.month):
                month_filtered_data.append(item)
        except (IndexError, ValueError):
            continue
    
    # 日付でグループ化
    grouped_schedule = {}
    for item in month_filtered_data:
        date = item['date']
        if date not in grouped_schedule:
            grouped_schedule[date] = []
        grouped_schedule[date].append({
            'time': item['time'],
            'title': item['title']
        })
    
    # 日付順にソート（年、月、日を個別に数値として扱う）
    def date_sort_key(date_str):
        year, month, day = map(int, date_str.split('.'))
        return (year, month, day)  # タプルで返すことで自然な順序付けを実現

    sorted_schedule = dict(sorted(grouped_schedule.items(), key=lambda x: date_sort_key(x[0])))
    
    return jsonify(sorted_schedule)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
