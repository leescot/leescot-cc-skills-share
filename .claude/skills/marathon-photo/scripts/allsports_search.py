#!/usr/bin/env python3
"""
AllSports 馬拉松照片搜尋腳本

使用方式:
    python allsports_search.py --event "高雄馬" --bib 32319
    python allsports_search.py --event-id 778854 --bib 32319
    python allsports_search.py --list-events --keyword "馬拉松"
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

BASE_URL = "https://allsports.tw"
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
        print(f"Error: 無法連線到 AllSports 網站: {e}", file=sys.stderr)
        return []

    # 從 JavaScript 中解析 events['master'] 資料
    # 格式: events['master'] = //{ ... JSON data ... }
    html = resp.text
    master_match = re.search(r"events\['master'\]\s*=\s*//\{\s*\n\s*(\{.+?\})\s*\n", html, re.DOTALL)

    if master_match:
        try:
            events_data = json.loads(master_match.group(1))
            for event_id, event_info in events_data.items():
                event = {
                    'id': int(event_id),
                    'event_code': str(event_id).zfill(8),
                    'name': event_info.get('name', ''),
                    'date': event_info.get('date', ''),
                }
                events.append(event)
        except json.JSONDecodeError as e:
            print(f"Warning: 解析 JSON 失敗: {e}", file=sys.stderr)

    # 本地過濾關鍵字
    if keyword:
        keyword_lower = keyword.lower()
        events = [e for e in events if keyword_lower in e['name'].lower()]

    # 依日期排序 (最新優先)
    events.sort(key=lambda e: e.get('date', ''), reverse=True)

    return events


def search_by_bib(event_id: int, bib_number: str) -> dict:
    """用號碼布搜尋照片"""
    # AllSports 搜尋 URL 格式: /view/{event_id}/{event_id}/zekken/{bib}/
    search_url = f"{BASE_URL}/view/{event_id}/{event_id}/zekken/{bib_number}/"

    result = {
        'bib_number': bib_number,
        'event_id': event_id,
        'search_url': search_url,
        'total_count': 0,
        'photos': [],
        'event_name': None,
        'event_date': None,
        'price': None,
        'error': None,
    }

    # 使用 AJAX API 取得照片數量
    count_url = f"{BASE_URL}/ajax/photo/count/{event_id}/{event_id}/zekken/{bib_number}/"
    try:
        resp = requests.get(count_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        count_data = resp.json()
        result['total_count'] = int(count_data.get('count', 0))
    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        print(f"Warning: 無法取得照片數量: {e}", file=sys.stderr)

    # 使用 AJAX API 取得照片列表
    list_url = f"{BASE_URL}/ajax/photo/list/{event_id}/{event_id}/zekken/{bib_number}/0/"
    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        photos_data = resp.json()

        for photo in photos_data:
            photo_info = {
                'photo_id': photo.get('id', ''),
                'time': photo.get('time', ''),
                'thumbnail': photo.get('image', ''),
                'detail': photo.get('detail', ''),
            }
            result['photos'].append(photo_info)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Warning: 無法取得照片列表: {e}", file=sys.stderr)

    # 從搜尋頁面取得活動名稱和價格
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 從 breadcrumb 取得活動名稱
        breadcrumb = soup.find('a', href=re.compile(rf'/event/\d*{event_id}\.html'))
        if breadcrumb:
            result['event_name'] = breadcrumb.get_text(strip=True)

        # 取得套餐價格
        price_elem = soup.find(string=re.compile(r'優惠価格.*元'))
        if price_elem:
            price_match = re.search(r'(\d+)\s*元', price_elem)
            if price_match:
                result['price'] = int(price_match.group(1))
    except requests.RequestException:
        pass

    return result


def get_event_detail(event_id: int) -> dict:
    """取得賽事詳細資訊"""
    # 賽事頁面需要 8 位數的 event_code
    event_code = str(event_id).zfill(8)
    url = f"{BASE_URL}/event/{event_code}.html"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 無法取得賽事資訊: {e}", file=sys.stderr)
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')

    detail = {
        'id': event_id,
        'event_code': event_code,
        'name': '',
        'date': '',
        'url': url,
        'locations': [],
    }

    # 取得活動名稱
    title = soup.find('h1')
    if title:
        title_text = title.get_text(strip=True)
        # 格式: "2026 高雄富邦馬拉松 (2026年1月11日)"
        name_match = re.match(r'(.+?)\s*\((\d{4})年(\d{1,2})月(\d{1,2})日\)', title_text)
        if name_match:
            detail['name'] = name_match.group(1).strip()
            detail['date'] = f"{name_match.group(2)}-{name_match.group(3).zfill(2)}-{name_match.group(4).zfill(2)}"
        else:
            detail['name'] = title_text

    # 取得拍攝地點列表
    location_elems = soup.find_all('em')
    for elem in location_elems:
        location = elem.get_text(strip=True)
        if location and location not in detail['locations']:
            detail['locations'].append(location)

    return detail


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇最新的活動 (日期最近)
    events.sort(key=lambda e: e.get('date', ''), reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='AllSports 馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--event-id', '-i', type=int, help='賽事 ID (直接指定)')
    parser.add_argument('--list-events', '-l', action='store_true', help='列出活動')
    parser.add_argument('--keyword', '-k', help='過濾活動關鍵字 (搭配 --list-events)')
    parser.add_argument('--detail', '-d', action='store_true', help='顯示賽事詳細資訊')
    parser.add_argument('--json', '-j', action='store_true', help='輸出 JSON 格式')

    args = parser.parse_args()

    # 列出活動模式
    if args.list_events:
        events = get_event_list(args.keyword)
        if args.json:
            print(json.dumps(events, ensure_ascii=False, indent=2))
        else:
            print(f"\n找到 {len(events)} 個活動:\n")
            for e in events[:20]:
                print(f"  [ID:{e['id']}] {e['date']} {e['name']}")
            if len(events) > 20:
                print(f"\n  ... 還有 {len(events) - 20} 個活動")
        return

    # 顯示賽事詳細資訊
    if args.detail and args.event_id:
        detail = get_event_detail(args.event_id)
        if args.json:
            print(json.dumps(detail, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"賽事詳細資訊")
            print(f"{'='*60}")
            print(f"ID: {detail['id']}")
            print(f"名稱: {detail['name']}")
            print(f"日期: {detail['date']}")
            print(f"頁面: {detail['url']}")
            if detail['locations']:
                print(f"\n拍攝地點:")
                for loc in detail['locations'][:10]:
                    print(f"  - {loc}")
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

        result = search_by_bib(event_id, args.bib)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"搜尋結果")
            print(f"{'='*60}")
            print(f"網站: AllSports")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"找到照片: {result['total_count']} 張")
            if result['price']:
                print(f"套餐價格: {result['price']} 元")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表 (前 10 張):\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. ID: {photo['photo_id']}  TIME: {photo['time']}")

                if len(result['photos']) > 10:
                    print(f"\n  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n搜尋結果頁面: {result['search_url']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
