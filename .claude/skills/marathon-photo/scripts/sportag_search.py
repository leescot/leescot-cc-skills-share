#!/usr/bin/env python3
"""
運動標籤 Sportag 馬拉松照片搜尋腳本

使用方式:
    python sportag_search.py --event "高雄馬拉松" --bib 32319
    python sportag_search.py --event-id 1215 --bib 32319
    python sportag_search.py --list-events --keyword "馬拉松"
"""

import argparse
import re
import sys
import json
from typing import Optional
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://www.sportag.net/web"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    url = f"{BASE_URL}/event.php"
    events = []
    page = 1

    while True:
        try:
            params = {'page': page} if page > 1 else {}
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
        except requests.RequestException as e:
            print(f"Error: 無法連線到運動標籤網站: {e}", file=sys.stderr)
            break

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 找到所有活動卡片
        event_cards = soup.find_all('a', href=re.compile(r'event-photo\.php\?event_id=\d+'))
        if not event_cards:
            break

        found_new = False
        for card in event_cards:
            href = card.get('href', '')
            event_id_match = re.search(r'event_id=(\d+)', href)
            if not event_id_match:
                continue

            event_id = event_id_match.group(1)

            # 取得活動名稱和日期
            text = card.get_text(strip=True)
            # 嘗試解析日期 (格式: YYYY-MM-DD)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            date = date_match.group(1) if date_match else ''

            # 清理名稱
            name = re.sub(r'\d{4}-\d{2}-\d{2}', '', text).strip()
            name = re.sub(r'\(購買原圖.*?\)', '', name).strip()

            # 取得照片數量
            photo_count = 0
            parent = card.find_parent()
            if parent:
                count_elem = parent.find(string=re.compile(r'^\d+$'))
                if count_elem:
                    photo_count = int(count_elem.strip())
                # 另一種方式：找圖片數量的元素
                count_div = parent.find('div', string=re.compile(r'^\d+$'))
                if count_div:
                    try:
                        photo_count = int(count_div.get_text(strip=True))
                    except ValueError:
                        pass

            event = {
                'id': int(event_id),
                'name': name,
                'date': date,
                'photo_count': photo_count,
            }

            # 檢查是否已存在
            if not any(e['id'] == event['id'] for e in events):
                # 過濾關鍵字
                if keyword is None:
                    events.append(event)
                    found_new = True
                else:
                    name_lower = event['name'].lower()
                    keyword_lower = keyword.lower()

                    # 完整匹配
                    if keyword_lower in name_lower:
                        events.append(event)
                        found_new = True
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
                        # 所有部分都要匹配
                        if all(part in name_lower for part in parts):
                            events.append(event)
                            found_new = True

        # 只抓前 3 頁，避免太慢
        if page >= 3 or not found_new:
            break
        page += 1

    return events


def search_by_bib(event_id: int, bib_number: str) -> dict:
    """用號碼布搜尋照片"""
    url = f"{BASE_URL}/event-photo.php"
    params = {
        'event_id': event_id,
        'code': bib_number
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
        return {'error': str(e)}

    soup = BeautifulSoup(resp.text, 'html.parser')

    result = {
        'bib_number': bib_number,
        'event_id': event_id,
        'search_url': f"{url}?event_id={event_id}&code={bib_number}",
        'total_count': 0,
        'photos': [],
        'event_name': None,
    }

    # 取得活動名稱
    title = soup.find('title')
    if title:
        title_text = title.get_text(strip=True)
        # 格式: "賽事: XXX - 運動標籤"
        name_match = re.search(r'賽事:\s*(.+?)\s*-\s*運動標籤', title_text)
        if name_match:
            result['event_name'] = name_match.group(1).strip()
            # 清理名稱
            result['event_name'] = re.sub(r'\(購買原圖.*?\)', '', result['event_name']).strip()

    # 取得照片數量 (從頁面上的數字)
    # 找 heading 中的數字
    count_heading = soup.find('h6')
    if count_heading:
        count_text = count_heading.get_text(strip=True)
        if count_text.isdigit():
            result['total_count'] = int(count_text)

    # 找照片 URL (從 photos.sportag.net)
    photo_urls = set()
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'photos.sportag.net' in src:
            photo_urls.add(src)

    # 也搜尋 background-image 或其他屬性
    for elem in soup.find_all(style=re.compile(r'photos\.sportag\.net')):
        style = elem.get('style', '')
        url_match = re.search(r'url\(["\']?(https://photos\.sportag\.net[^"\')\s]+)', style)
        if url_match:
            photo_urls.add(url_match.group(1))

    # 從 link 的 ID 提取照片資訊
    photo_links = soup.find_all('a', href='#', string=re.compile(r'ID:\s*\d+'))
    for link in photo_links:
        text = link.get_text(strip=True)
        id_match = re.search(r'ID:\s*(\d+)', text)
        time_match = re.search(r'(\d{2}:\d{2}:\d{2})', text)
        if id_match:
            photo_info = {
                'photo_id': id_match.group(1),
                'time': time_match.group(1) if time_match else '',
            }
            result['photos'].append(photo_info)

    # 如果沒有找到照片數量，用照片列表的長度
    if result['total_count'] == 0:
        result['total_count'] = len(result['photos'])

    # 添加照片 URL 到結果
    result['photo_urls'] = list(photo_urls)

    return result


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇最新的活動 (日期最近)
    events.sort(key=lambda e: e.get('date', ''), reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='運動標籤 Sportag 馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--event-id', '-i', type=int, help='賽事 ID (直接指定)')
    parser.add_argument('--list-events', '-l', action='store_true', help='列出活動')
    parser.add_argument('--keyword', '-k', help='過濾活動關鍵字 (搭配 --list-events)')
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
                count_str = f"({e['photo_count']:,} 張)" if e['photo_count'] else ""
                print(f"  [ID:{e['id']}] {e['date']} {e['name']} {count_str}")
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
            print(f"網站: 運動標籤 Sportag")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"找到照片: {result['total_count']} 張")
            print(f"{'='*60}")

            if result['photos']:
                print(f"\n照片列表:\n")
                for i, photo in enumerate(result['photos'][:10], 1):
                    print(f"  {i}. ID: {photo['photo_id']}  時間: {photo['time']}")

                if len(result['photos']) > 10:
                    print(f"\n  ... 還有 {len(result['photos']) - 10} 張照片")

            print(f"\n搜尋結果頁面: {result['search_url']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
