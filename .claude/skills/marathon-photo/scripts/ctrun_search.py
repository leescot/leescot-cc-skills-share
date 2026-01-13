#!/usr/bin/env python3
"""
全統運動 CTRun 馬拉松照片搜尋腳本

使用方式:
    python ctrun_search.py --event "屏東馬" --bib 50282
    python ctrun_search.py --event-id 231 --bib 50282
    python ctrun_search.py --list-events --keyword "馬拉松"
"""

import argparse
import re
import sys
import json
from typing import Optional
from urllib.parse import urljoin, quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://www.ctrun.com.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    # 總是從主頁面取得活動列表，然後在本地過濾
    url = f"{BASE_URL}/Album"

    events = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 無法連線到全統運動網站: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 找到所有活動卡片
    event_links = soup.find_all('a', href=re.compile(r'/Album/[Dd]etail\?EventMain_ID=\d+'))

    for link in event_links:
        href = link.get('href', '')
        event_id_match = re.search(r'EventMain_ID=(\d+)', href)
        if not event_id_match:
            continue

        event_id = int(event_id_match.group(1))

        # 檢查是否已存在
        if any(e['id'] == event_id for e in events):
            continue

        # 取得活動名稱
        parent = link.find_parent('div', class_='pri_table_list')
        if not parent:
            parent = link.find_parent()

        name = ''
        date = ''
        location = ''

        # 嘗試從 h6, h4 標籤取得年份和名稱 (h6=年份, h4=活動名)
        h6 = parent.find('h6') if parent else None
        h4 = parent.find('h4') if parent else None

        if h6:
            year = h6.get_text(strip=True)
            if h4:
                event_name = h4.get_text(strip=True)
                name = f"{year} {event_name}"

        if not name:
            # 從連結文字取得
            name = link.get_text(strip=True)
            if not name:
                img = link.find('img')
                if img:
                    name = img.get('alt', '') or img.get('title', '')

        # 嘗試取得日期
        date_elem = parent.find(string=re.compile(r'\d{4}年\d{1,2}月\d{1,2}日')) if parent else None
        if date_elem:
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_elem)
            if date_match:
                date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"

        # 嘗試取得地點
        location_icons = parent.find_all('i', class_=re.compile(r'fa-map')) if parent else []
        for icon in location_icons:
            loc_text = icon.find_next_sibling(string=True)
            if loc_text:
                location = loc_text.strip()
                break

        if name:
            events.append({
                'id': event_id,
                'name': name.strip(),
                'date': date,
                'location': location,
            })

    # 本地過濾關鍵字
    if keyword:
        keyword_lower = keyword.lower()
        events = [e for e in events if keyword_lower in e['name'].lower()]

    return events


def search_by_bib(event_id: int, bib_number: str) -> dict:
    """用號碼布搜尋照片"""
    url = f"{BASE_URL}/Album/NumPhotos"
    params = {
        'EventMain_ID': event_id,
        'Num': bib_number
    }

    result = {
        'bib_number': bib_number,
        'event_id': event_id,
        'search_url': f"{BASE_URL}/Album/NumPhotos?EventMain_ID={event_id}&Num={bib_number}",
        'total_count': 0,
        'photos': [],
        'event_name': None,
        'error': None,
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
        result['error'] = str(e)
        return result

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 取得活動名稱
    title = soup.find('h2')
    if title:
        result['event_name'] = title.get_text(strip=True)

    # 找照片 URL (Azure Blob Storage)
    photo_links = soup.find_all('a', href=re.compile(r'ctrunstorage\.blob\.core\.windows\.net'))

    for link in photo_links:
        href = link.get('href', '')
        if href:
            # 取得類別
            category = ''
            img = link.find('img')
            if img:
                alt = img.get('alt', '')
                if alt:
                    category = alt

            photo_info = {
                'url': href,
                'category': category,
                'filename': href.split('/')[-1] if '/' in href else '',
            }
            result['photos'].append(photo_info)

    result['total_count'] = len(result['photos'])

    return result


def get_event_detail(event_id: int) -> dict:
    """取得賽事詳細資訊"""
    url = f"{BASE_URL}/Album/detail"
    params = {'EventMain_ID': event_id}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 無法取得賽事資訊: {e}", file=sys.stderr)
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')

    detail = {
        'id': event_id,
        'name': '',
        'bib_coverage': '',
        'categories': [],
    }

    # 取得活動名稱
    title = soup.find('h2')
    if title:
        detail['name'] = title.get_text(strip=True)

    # 取得號碼布標記率
    coverage_text = soup.find(string=re.compile(r'已經有.*的照片有標記號碼布'))
    if coverage_text:
        match = re.search(r'(\d+\.?\d*)%', coverage_text)
        if match:
            detail['bib_coverage'] = match.group(1) + '%'

    # 取得相簿類別
    category_links = soup.find_all('a', href=re.compile(r'/Album/Photos\?.*Category='))
    for link in category_links:
        href = link.get('href', '')
        cat_match = re.search(r'Category=([^&]+)', href)
        if cat_match:
            category = cat_match.group(1)
            # 取得照片數量
            count_elem = link.find_next('h6', string=re.compile(r'共.*張'))
            count = 0
            if count_elem:
                count_match = re.search(r'(\d+)', count_elem.get_text())
                if count_match:
                    count = int(count_match.group(1))

            if category not in [c['name'] for c in detail['categories']]:
                detail['categories'].append({
                    'name': category,
                    'photo_count': count,
                })

    return detail


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇最新的活動 (ID 最大的通常是最新的)
    events.sort(key=lambda e: e['id'], reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='全統運動 CTRun 馬拉松照片搜尋')
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
                date_str = f"{e['date']} " if e['date'] else ""
                print(f"  [ID:{e['id']}] {date_str}{e['name']}")
            if len(events) > 20:
                print(f"\n  ... 還有 {len(events) - 20} 個活動")
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
            print(f"網站: 全統運動 CTRun")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"找到照片: {result['total_count']} 張")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表:\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. {photo['url']}")
                    if photo['category']:
                        print(f"     類別: {photo['category']}")
                    print()

                if len(result['photos']) > 10:
                    print(f"  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n搜尋結果頁面: {result['search_url']}")

    # 顯示賽事詳細資訊
    elif args.detail and args.event_id:
        detail = get_event_detail(args.event_id)
        if args.json:
            print(json.dumps(detail, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"賽事詳細資訊")
            print(f"{'='*60}")
            print(f"ID: {detail['id']}")
            print(f"名稱: {detail['name']}")
            print(f"號碼布標記率: {detail['bib_coverage']}")
            print(f"\n相簿類別:")
            for cat in detail['categories']:
                print(f"  - {cat['name']}: {cat['photo_count']} 張")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
