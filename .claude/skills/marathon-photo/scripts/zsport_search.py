#!/usr/bin/env python3
"""
ZSport 馬拉松照片搜尋腳本

使用方式:
    python zsport_search.py --event "高雄馬" --bib 32319
    python zsport_search.py --activity-id 254 --bib 32319
    python zsport_search.py --list-events --keyword "馬拉松"
"""

import argparse
import re
import sys
import json
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://www.zsport.com.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    url = f"{BASE_URL}/"
    events = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 無法連線到 ZSport 網站: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 找所有活動連結 (格式: /activity/{id})
    for link in soup.find_all('a', href=re.compile(r'^/activity/\d+')):
        href = link.get('href', '')
        match = re.search(r'/activity/(\d+)', href)
        if not match:
            continue

        activity_id = int(match.group(1))
        name = link.get_text(strip=True)

        # 跳過空名稱
        if not name:
            continue

        # 取得照片數量 (在 row 容器中找)
        photo_count = 0
        days_left = None

        # 往上找到 row 容器 (包含活動名稱和照片數量)
        row = link.find_parent('div', class_='row')
        if not row:
            row = link.find_parent('tr')
        if not row:
            # 嘗試往上找幾層
            parent = link.parent
            for _ in range(5):
                if parent is None:
                    break
                row_text = parent.get_text()
                if '張' in row_text:
                    row = parent
                    break
                parent = parent.parent

        if row:
            row_text = row.get_text()
            # 尋找照片數量
            count_match = re.search(r'([\d,]+)\s*張', row_text)
            if count_match:
                photo_count = int(count_match.group(1).replace(',', ''))

            # 檢查是否有剩餘天數標記
            days_match = re.search(r'\(剩(\d+)天\)', row_text)
            if days_match:
                days_left = int(days_match.group(1))

        event = {
            'id': activity_id,
            'name': name,
            'photo_count': photo_count,
            'days_left': days_left,
        }

        # 避免重複
        if not any(e['id'] == activity_id for e in events):
            events.append(event)

    # 本地過濾關鍵字
    if keyword:
        keyword_lower = keyword.lower()
        events = [e for e in events if keyword_lower in e['name'].lower()]

    # 依 ID 排序 (最新優先)
    events.sort(key=lambda e: e['id'], reverse=True)

    return events


def search_by_bib(activity_id: int, bib_number: str, max_results: int = 100) -> dict:
    """用號碼布搜尋照片"""
    all_photos = []
    page = 1
    total_count = 0
    event_name = None
    event_date = None

    while True:
        url = f"{BASE_URL}/api/activity/{activity_id}"
        params = {
            'page': page,
            'q': bib_number,
        }

        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
            return {'error': str(e)}
        except json.JSONDecodeError as e:
            print(f"Error: JSON 解析失敗: {e}", file=sys.stderr)
            return {'error': str(e)}

        if data.get('rtncode') != 0:
            error_msg = data.get('errcause', 'Unknown error')
            print(f"Error: API 回應錯誤: {error_msg}", file=sys.stderr)
            return {'error': error_msg}

        result_data = data.get('data', {})

        # 取得活動資訊 (第一頁)
        if page == 1:
            event_name = result_data.get('name')
            event_date = result_data.get('action_time', '')[:10] if result_data.get('action_time') else ''

        photo_data = result_data.get('photo', {})
        photos = photo_data.get('data', [])
        total_count = photo_data.get('total', 0)

        all_photos.extend(photos)

        # 檢查是否還有更多頁
        current_page = photo_data.get('current_page', 1)
        last_page = (total_count + photo_data.get('per_page', 49) - 1) // photo_data.get('per_page', 49)

        if current_page >= last_page or len(all_photos) >= max_results or not photos:
            break

        page += 1

    # 整理結果
    result = {
        'bib_number': bib_number,
        'activity_id': activity_id,
        'search_url': f"{BASE_URL}/activity/{activity_id}",
        'total_count': total_count,
        'fetched_count': len(all_photos),
        'photos': [],
        'event_name': event_name,
        'event_date': event_date,
        'price': None,
    }

    # 整理照片資訊
    for photo in all_photos:
        # 照片 URL 格式: /img/photo/{activity_id}/{sha1}_s.webp (縮圖)
        sha1 = photo.get('sha1', '')
        photo_info = {
            'photo_id': photo.get('id'),
            'sha1': sha1,
            'thumbnail': f"{BASE_URL}/img/photo/{activity_id}/{sha1}_s.webp" if sha1 else '',
            'time': photo.get('shoot_time', ''),
            'photographer': photo.get('author_name', ''),
            'price': photo.get('price'),
        }
        result['photos'].append(photo_info)

        # 記錄價格
        if result['price'] is None and photo.get('price'):
            result['price'] = photo.get('price')

    return result


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇最新的活動 (ID 最大)
    events.sort(key=lambda e: e['id'], reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='ZSport 馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--activity-id', '-a', type=int, help='活動 ID (直接指定)')
    parser.add_argument('--list-events', '-l', action='store_true', help='列出活動')
    parser.add_argument('--keyword', '-k', help='過濾活動關鍵字 (搭配 --list-events)')
    parser.add_argument('--json', '-j', action='store_true', help='輸出 JSON 格式')
    parser.add_argument('--max', '-m', type=int, default=100, help='最大回傳照片數 (預設: 100)')

    args = parser.parse_args()

    # 列出活動模式
    if args.list_events:
        events = get_event_list(args.keyword)
        if args.json:
            print(json.dumps(events, ensure_ascii=False, indent=2))
        else:
            print(f"\n找到 {len(events)} 個活動:\n")
            for e in events[:30]:
                days_info = f" (剩{e['days_left']}天)" if e.get('days_left') else ""
                print(f"  [ID:{e['id']}] {e['name']}{days_info} ({e['photo_count']:,} 張)")
            if len(events) > 30:
                print(f"\n  ... 還有 {len(events) - 30} 個活動")
        return

    # 搜尋模式
    if args.bib:
        activity_id = args.activity_id

        # 如果沒有直接給 activity_id，從 event 關鍵字找
        if not activity_id and args.event:
            event = find_event_by_keyword(args.event)
            if event:
                activity_id = event['id']
                if not args.json:
                    print(f"找到活動: {event['name']} (ID: {activity_id})")
            else:
                print(f"Error: 找不到符合 '{args.event}' 的活動", file=sys.stderr)
                sys.exit(1)

        if not activity_id:
            print("Error: 請提供 --event 或 --activity-id", file=sys.stderr)
            sys.exit(1)

        result = search_by_bib(activity_id, args.bib, args.max)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"搜尋結果")
            print(f"{'='*60}")
            print(f"網站: ZSport")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"日期: {result.get('event_date', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"找到照片: {result['total_count']} 張")
            if result['price']:
                print(f"單張價格: {result['price']} 元")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表 (前 10 張):\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. ID: {photo['photo_id']}")
                    print(f"     拍攝時間: {photo['time']}")
                    print(f"     攝影師: {photo['photographer']}")
                    print()

                if len(result['photos']) > 10:
                    print(f"  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n搜尋結果頁面: {result['search_url']}")
            print(f"(請在網站上輸入號碼布 {result['bib_number']} 搜尋)")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
