#!/usr/bin/env python3
"""
好拍 GoodShot 馬拉松照片搜尋腳本

使用方式:
    python goodshot_search.py --event "高雄馬拉松" --bib 32319
    python goodshot_search.py --competition-id 303 --bib 32319
    python goodshot_search.py --list-events --keyword "馬拉松"
"""

import argparse
import sys
import json
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://goodshot.com.tw"
API_BASE = f"{BASE_URL}/api/front/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    url = f"{API_BASE}/competition"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"Error: 無法連線到好拍網站: {e}", file=sys.stderr)
        return []

    if data.get('code') != 200:
        print(f"Error: API 回應錯誤: {data}", file=sys.stderr)
        return []

    events = []
    for item in data.get('data', []):
        event = {
            'id': item['id'],
            'name': item['title'],
            'date': item['date'][:10] if item.get('date') else '',
            'location': item.get('county', ''),
            'photo_count': item.get('photosNum', 0),
            'photographers': item.get('photographersNum', 0),
        }

        # 過濾關鍵字
        if keyword is None:
            events.append(event)
        else:
            name_lower = event['name'].lower()
            keyword_lower = keyword.lower()

            # 完整匹配或分詞匹配
            if keyword_lower in name_lower:
                events.append(event)
            else:
                # 分詞匹配
                common_words = ['馬拉松', '路跑', '越野', '半馬', '全馬', '超馬']
                parts = []
                remaining = keyword_lower
                for word in common_words:
                    if word in remaining:
                        parts.append(word)
                        remaining = remaining.replace(word, ' ')
                for part in remaining.split():
                    if part.strip():
                        parts.append(part.strip())

                if not parts:
                    parts = [keyword_lower]

                if all(part in name_lower for part in parts):
                    events.append(event)

    return events


def search_by_bib(competition_id: int, bib_number: str, fuzzy: bool = False, max_results: int = 100) -> dict:
    """用號碼布搜尋照片"""
    all_photos = []
    page = 0
    row = 50  # 每頁數量

    while True:
        url = f"{API_BASE}/competition/{competition_id}/photo/search"
        params = {
            'row': row,
            'page': page,
            'bibNum': bib_number,
            'fuzzy': 'true' if fuzzy else 'false'
        }

        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
            return {'error': str(e)}

        if data.get('code') != 200:
            print(f"Error: API 回應錯誤: {data}", file=sys.stderr)
            return {'error': 'API error'}

        photos = data.get('data', {}).get('list', [])
        total_count = data.get('data', {}).get('count', 0)

        all_photos.extend(photos)

        # 檢查是否還有更多頁
        if len(all_photos) >= total_count or len(all_photos) >= max_results or not photos:
            break

        page += 1

    # 整理結果
    result = {
        'bib_number': bib_number,
        'competition_id': competition_id,
        'total_count': data.get('data', {}).get('count', 0),
        'fetched_count': len(all_photos),
        'fuzzy_search': fuzzy,
        'photos': [],
        'event_name': None,
        'event_date': None,
    }

    # 取得活動資訊
    if all_photos:
        first_photo = all_photos[0]
        result['event_name'] = first_photo.get('competitionTitle')
        result['event_date'] = first_photo.get('competitionDate', '')[:10] if first_photo.get('competitionDate') else ''

    # 整理照片資訊
    for photo in all_photos:
        photo_info = {
            'id': photo['id'],
            'url': f"{BASE_URL}{photo['coverImg']}",
            'take_time': photo.get('takeTime', '')[:19].replace('T', ' ') if photo.get('takeTime') else '',
            'photographer': photo.get('ownerName', ''),
            'bib_numbers': [photo.get(f'bibNum{i}') for i in ['', '1', '2', '3', '4', '5', '6', '7', '8'] if photo.get(f'bibNum{i}')],
        }
        result['photos'].append(photo_info)

    # 產生賽事頁面 URL (GoodShot 不支援 URL 參數預填搜尋)
    result['search_url'] = f"{BASE_URL}/competitions/{competition_id}/competitionPG"

    return result


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇照片數量最多的活動
    events.sort(key=lambda e: e['photo_count'], reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='好拍 GoodShot 馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--competition-id', '-c', type=int, help='賽事 ID (直接指定)')
    parser.add_argument('--fuzzy', '-f', action='store_true', help='使用模糊搜尋')
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
            for e in events[:20]:
                print(f"  [ID:{e['id']}] {e['date']} {e['name']} ({e['photo_count']:,} 張)")
            if len(events) > 20:
                print(f"\n  ... 還有 {len(events) - 20} 個活動")
        return

    # 搜尋模式
    if args.bib:
        competition_id = args.competition_id

        # 如果沒有直接給 competition_id，從 event 關鍵字找
        if not competition_id and args.event:
            event = find_event_by_keyword(args.event)
            if event:
                competition_id = event['id']
                if not args.json:
                    print(f"找到活動: {event['name']} (ID: {competition_id})")
            else:
                print(f"Error: 找不到符合 '{args.event}' 的活動", file=sys.stderr)
                sys.exit(1)

        if not competition_id:
            print("Error: 請提供 --event 或 --competition-id", file=sys.stderr)
            sys.exit(1)

        result = search_by_bib(competition_id, args.bib, args.fuzzy, args.max)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"搜尋結果")
            print(f"{'='*60}")
            print(f"網站: 好拍 GoodShot")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"日期: {result.get('event_date', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"搜尋模式: {'模糊搜尋' if result['fuzzy_search'] else '精確搜尋'}")
            print(f"{'='*60}")
            print(f"找到照片: {result['total_count']} 張")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表 (前 10 張):\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. {photo['url']}")
                    print(f"     拍攝時間: {photo['take_time']}")
                    print(f"     攝影師: {photo['photographer']}")
                    print()

                if len(result['photos']) > 10:
                    print(f"  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n網站搜尋頁面: {result['search_url']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
