#!/usr/bin/env python3
"""
RaceShot 運動拍檔 馬拉松照片搜尋腳本

使用方式:
    python raceshot_search.py --event "台北馬" --bib 13213
    python raceshot_search.py --event-id 251203 --bib 13213
    python raceshot_search.py --list-events --keyword "馬拉松"
"""

import argparse
import json
import sys
import urllib.parse
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://api.raceshot.app/api/v1/public"
WEB_BASE = "https://raceshot.app"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None, limit: int = 50) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    events = []
    page = 1

    while len(events) < limit:
        params = {
            'page': page,
            'limit': 50,
            'sortOrder': 'DESC',
            'minPublishedPhotos': '1',  # 只顯示有照片的活動
        }

        if keyword:
            params['search'] = keyword

        try:
            resp = requests.get(f"{API_BASE}/events", params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Error: 無法連線到 RaceShot API: {e}", file=sys.stderr)
            return events
        except json.JSONDecodeError as e:
            print(f"Error: JSON 解析失敗: {e}", file=sys.stderr)
            return events

        page_events = data.get('events', [])
        if not page_events:
            break

        for e in page_events:
            # categories 可能是 JSON 字串
            categories = e.get('categories', [])
            if isinstance(categories, str):
                try:
                    categories = json.loads(categories)
                except json.JSONDecodeError:
                    categories = []

            events.append({
                'id': e.get('id'),
                'name': e.get('name'),
                'date': e.get('date'),
                'location': e.get('location', '').strip(),
                'photo_count': e.get('published_photo_count', 0),
                'categories': categories if isinstance(categories, list) else [],
                'sales_end_date': e.get('sales_end_date'),
            })

        # 檢查是否還有更多頁
        total = data.get('total', 0)
        if len(events) >= total or len(events) >= limit:
            break

        page += 1

    return events[:limit]


def search_by_bib(event_id: str, bib_number: str) -> dict:
    """用號碼布搜尋照片

    注意: RaceShot API 回傳該活動所有照片，
    號碼布篩選需在 client-side 進行。
    """
    url = f"{API_BASE}/photos"
    params = {'eventId': event_id}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
        return {'error': str(e)}
    except json.JSONDecodeError as e:
        print(f"Error: JSON 解析失敗: {e}", file=sys.stderr)
        return {'error': str(e)}

    all_photos = data.get('photos', [])

    # Client-side 篩選號碼布
    matching_photos = []
    for photo in all_photos:
        bib_str = photo.get('bib_number', '[]')
        # bib_number 是 JSON 字串陣列
        try:
            bibs = json.loads(bib_str)
            if isinstance(bibs, list) and bib_number in bibs:
                matching_photos.append(photo)
        except json.JSONDecodeError:
            # 如果解析失敗，用字串比對
            if bib_number in bib_str:
                matching_photos.append(photo)

    # 取得活動資訊
    event_info = get_event_info(event_id)

    result = {
        'bib_number': bib_number,
        'event_id': event_id,
        'event_name': event_info.get('name') if event_info else None,
        'event_date': event_info.get('date') if event_info else None,
        'search_url': f"{WEB_BASE}/events/{event_id}",
        'total_event_photos': len(all_photos),
        'total_count': len(matching_photos),
        'photos': [],
        'price': 169,  # 固定價格
    }

    # 整理照片資訊
    for photo in matching_photos:
        photo_info = {
            'photo_id': photo.get('photo_id'),
            'time': photo.get('create_date'),
            'capture_timestamp': photo.get('capture_timestamp'),
            'photographer': photo.get('photographer_name'),
            'location': photo.get('location'),
            'bibs': photo.get('bib_number'),
        }
        result['photos'].append(photo_info)

    # 按拍攝時間排序
    result['photos'].sort(key=lambda p: p.get('capture_timestamp') or 0)

    return result


def get_event_info(event_id: str) -> Optional[dict]:
    """取得活動詳細資訊"""
    events = get_event_list(limit=200)
    for e in events:
        if str(e.get('id')) == str(event_id):
            return e
    return None


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword=keyword, limit=10)

    if not events:
        return None

    # 選擇照片數最多的活動 (通常是主要賽事)
    events.sort(key=lambda e: e.get('photo_count', 0), reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='RaceShot 運動拍檔 馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--event-id', '-i', help='活動 ID (直接指定)')
    parser.add_argument('--list-events', '-l', action='store_true', help='列出活動')
    parser.add_argument('--keyword', '-k', help='過濾活動關鍵字 (搭配 --list-events)')
    parser.add_argument('--json', '-j', action='store_true', help='輸出 JSON 格式')
    parser.add_argument('--limit', '-n', type=int, default=30, help='最大活動數 (預設: 30)')

    args = parser.parse_args()

    # 列出活動模式
    if args.list_events:
        events = get_event_list(keyword=args.keyword, limit=args.limit)
        if args.json:
            print(json.dumps(events, ensure_ascii=False, indent=2))
        else:
            print(f"\n找到 {len(events)} 個活動:\n")
            for e in events:
                categories = ', '.join(e.get('categories', [])) if e.get('categories') else ''
                cat_str = f" [{categories}]" if categories else ""
                print(f"  [{e['id']}] {e['name']}{cat_str}")
                print(f"       {e['date']} | {e['location']} | {e['photo_count']:,} 張")
        return

    # 搜尋模式
    if args.bib:
        event_id = args.event_id

        # 如果沒有直接給 event_id，從 event 關鍵字找
        if not event_id and args.event:
            event = find_event_by_keyword(args.event)
            if event:
                event_id = event['id']
                if not args.json:
                    print(f"找到活動: {event['name']} (ID: {event_id})")
            else:
                print(f"Error: 找不到符合 '{args.event}' 的活動", file=sys.stderr)
                sys.exit(1)

        if not event_id:
            print("Error: 請提供 --event 或 --event-id", file=sys.stderr)
            sys.exit(1)

        if not args.json:
            print(f"正在載入活動照片 (可能需要較長時間)...")

        result = search_by_bib(str(event_id), args.bib)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)

            print(f"\n{'='*60}")
            print(f"搜尋結果")
            print(f"{'='*60}")
            print(f"網站: RaceShot 運動拍檔")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"日期: {result.get('event_date', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"活動總照片: {result['total_event_photos']:,} 張")
            print(f"找到照片: {result['total_count']} 張")
            print(f"單張價格: NT${result['price']}")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表 (前 10 張):\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. ID: {photo['photo_id']}")
                    print(f"     拍攝時間: {photo['time']}")
                    print(f"     攝影師: {photo['photographer']}")
                    print(f"     地點: {photo['location']}")
                    print()

                if len(result['photos']) > 10:
                    print(f"  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n搜尋結果頁面: {result['search_url']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
