#!/usr/bin/env python3
"""
Phomi 瘋迷馬拉松照片搜尋腳本

使用方式:
    python phomi_search.py --event "高雄馬拉松" --bib 32319
    python phomi_search.py --act-code 83058571 --bib 32319
    python phomi_search.py --list-events --keyword "馬拉松"
"""

import argparse
import re
import sys
import json
from urllib.parse import urljoin, quote
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 請先安裝必要套件: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

BASE_URL = "http://www.phomi.com.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_event_list(keyword: Optional[str] = None) -> list[dict]:
    """取得活動列表，可選擇性過濾關鍵字"""
    # 使用動態載入的 API 端點
    url = f"{BASE_URL}/activity-list-load.php"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 無法連線到 Phomi 網站: {e}", file=sys.stderr)
        return []

    # 將 HTML 片段包裝成完整的 table 結構
    html_content = f"<table>{resp.text}</table>"
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []

    # 找到活動表格的所有行
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 5:
            # 尋找活動連結
            link = cells[1].find('a')
            if link and 'ActCode=' in link.get('href', ''):
                act_code_match = re.search(r'ActCode=(\d+)', link['href'])
                if act_code_match:
                    event = {
                        'date': cells[0].get_text(strip=True),
                        'name': link.get_text(strip=True),
                        'act_code': act_code_match.group(1),
                        'city': cells[2].get_text(strip=True),
                        'photographers': cells[3].get_text(strip=True),
                        'photo_count': cells[4].get_text(strip=True),
                    }

                    # 過濾關鍵字 (支援分詞匹配)
                    if keyword is None:
                        events.append(event)
                    else:
                        # 將關鍵字分解，所有詞都要在名稱中出現
                        # 例如 "高雄馬拉松" 會分解為 ["高雄", "馬拉松"]
                        name_lower = event['name'].lower()
                        keyword_lower = keyword.lower()

                        # 先嘗試完整匹配
                        if keyword_lower in name_lower:
                            events.append(event)
                        else:
                            # 嘗試分詞匹配 (中文以2-4字為單位)
                            # 簡單策略：檢查關鍵字中的每個中文字詞是否出現
                            parts = []
                            # 常見的馬拉松相關詞彙
                            common_words = ['馬拉松', '路跑', '越野', '半馬', '全馬', '超馬']
                            remaining = keyword_lower
                            for word in common_words:
                                if word in remaining:
                                    parts.append(word)
                                    remaining = remaining.replace(word, ' ')
                            # 剩餘的當作地名或活動名
                            for part in remaining.split():
                                if part.strip():
                                    parts.append(part.strip())

                            # 如果沒有分解成功，就用原本的關鍵字
                            if not parts:
                                parts = [keyword_lower]

                            # 所有部分都要匹配
                            if all(part in name_lower for part in parts):
                                events.append(event)

    return events


def search_by_bib(act_code: str, bib_number: str) -> dict:
    """用號碼布搜尋照片"""
    url = f"{BASE_URL}/bib-found-photo.php?bibtxt={bib_number}&ActCode={act_code}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error: 搜尋失敗: {e}", file=sys.stderr)
        return {'error': str(e)}

    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {
        'bib_number': bib_number,
        'act_code': act_code,
        'search_url': url,
        'exact_matches': 0,
        'possible_matches': 0,
        'more_url': None,
        'event_name': None,
        'event_date': None,
    }

    # 解析標題取得活動資訊
    title = soup.find('h3')
    if title:
        title_text = title.get_text(strip=True)
        result['event_name'] = title_text.split('-')[1] if '-' in title_text else title_text

        # 尋找日期
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title_text)
        if date_match:
            result['event_date'] = date_match.group(1)

    # 解析找到的照片數量
    page_text = soup.get_text()

    # 尋找 "找到XXX號碼布照片N張"
    exact_match = re.search(r'找到.*?照片(\d+)張', page_text)
    if exact_match:
        result['exact_matches'] = int(exact_match.group(1))

    # 尋找 "更多...可能是XXX號的相片，N張"
    more_link = soup.find('a', href=re.compile(r'bib-found-photo-more\.php'))
    if more_link:
        more_text = more_link.get_text(strip=True)
        possible_match = re.search(r'(\d+)張', more_text)
        if possible_match:
            result['possible_matches'] = int(possible_match.group(1))
        result['more_url'] = urljoin(BASE_URL, more_link['href'])

    return result


def find_event_by_keyword(keyword: str) -> Optional[dict]:
    """根據關鍵字找到最佳匹配的活動"""
    events = get_event_list(keyword)

    if not events:
        return None

    # 選擇照片數量最多的活動
    def get_photo_count(event):
        match = re.search(r'(\d+)', event['photo_count'].replace(',', ''))
        return int(match.group(1)) if match else 0

    events.sort(key=get_photo_count, reverse=True)
    return events[0]


def main():
    parser = argparse.ArgumentParser(description='Phomi 瘋迷馬拉松照片搜尋')
    parser.add_argument('--event', '-e', help='活動名稱關鍵字')
    parser.add_argument('--bib', '-b', help='號碼布號碼')
    parser.add_argument('--act-code', '-a', help='活動代碼 (直接指定)')
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
            for e in events[:20]:  # 只顯示前 20 個
                print(f"  [{e['act_code']}] {e['date']} {e['name']} ({e['photo_count']})")
            if len(events) > 20:
                print(f"\n  ... 還有 {len(events) - 20} 個活動")
        return

    # 搜尋模式
    if args.bib:
        act_code = args.act_code

        # 如果沒有直接給 act_code，從 event 關鍵字找
        if not act_code and args.event:
            event = find_event_by_keyword(args.event)
            if event:
                act_code = event['act_code']
                if not args.json:
                    print(f"找到活動: {event['name']} (ActCode: {act_code})")
            else:
                print(f"Error: 找不到符合 '{args.event}' 的活動", file=sys.stderr)
                sys.exit(1)

        if not act_code:
            print("Error: 請提供 --event 或 --act-code", file=sys.stderr)
            sys.exit(1)

        result = search_by_bib(act_code, args.bib)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"搜尋結果")
            print(f"{'='*50}")
            print(f"網站: Phomi 瘋迷")
            print(f"活動: {result.get('event_name', 'N/A')}")
            print(f"日期: {result.get('event_date', 'N/A')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*50}")
            print(f"精確匹配: {result['exact_matches']} 張")
            print(f"可能相關: {result['possible_matches']} 張")
            print(f"{'='*50}")
            print(f"搜尋結果頁面:")
            print(f"  {result['search_url']}")
            if result['more_url']:
                print(f"更多可能照片:")
                print(f"  {result['more_url']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
