#!/usr/bin/env python3
"""
捷安 (Soonnet) 馬拉松照片搜尋腳本

使用方式:
    python soonnet_search.py -e "高雄" -b 12244       # 用關鍵字搜尋
    python soonnet_search.py -a 1376 -b 13213        # 用活動 ID 搜尋
    python soonnet_search.py -l -k "馬拉松"          # 列出有照片的活動
    python soonnet_search.py --scan                  # 掃描所有有照片的活動

API 端點:
    - GetConfigByActivityId: 取得活動配置 (照片數、攝影師)
    - Get: 取得活動基本資訊
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Optional

BASE_URL = "https://www.soonnetmall.com"
API_URL = "https://apimall.soonnetmall.com/api/services/app"

# 台/臺 轉換表
TAIWAN_CHAR_MAP = {
    '台': '臺',
    '臺': '台',
}

# 活動 ID 掃描範圍 (根據已知活動 ID 估計)
SCAN_RANGES = [
    (1320, 1420),   # 2025 年活動
    (2600, 2780),   # 2025-2026 年活動 (渣打馬 2672, 高雄馬 2765)
]


def normalize_keyword(keyword: str) -> list[str]:
    """產生關鍵字的變體 (處理 台/臺 轉換)"""
    variants = [keyword]
    for char, replacement in TAIWAN_CHAR_MAP.items():
        if char in keyword:
            variant = keyword.replace(char, replacement)
            if variant not in variants:
                variants.append(variant)
    return variants


def api_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """呼叫 GET API"""
    url = f"{API_URL}{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success"):
                return data.get("result")
    except (urllib.error.URLError, json.JSONDecodeError):
        pass
    return None


def get_activity_config(activity_id: int) -> Optional[dict]:
    """取得活動配置 (包含照片數和攝影師)"""
    result = api_get("/Activity/GetConfigByActivityId", {"activityId": activity_id})
    if result:
        photo_count = sum(item.get("photoCount", 0) for item in result.get("list", []))
        return {
            "id": activity_id,
            "title": result.get("title"),
            "photo_count": photo_count,
            "photographers": result.get("sheyinCount", 0),
        }
    return None


def scan_activities(verbose: bool = False) -> list[dict]:
    """掃描有照片的活動"""
    activities = []
    total_ids = sum(end - start for start, end in SCAN_RANGES)
    checked = 0

    for start, end in SCAN_RANGES:
        for aid in range(start, end):
            checked += 1
            if verbose:
                print(f"\r掃描中: {checked}/{total_ids}...", end="", file=sys.stderr)

            config = get_activity_config(aid)
            if config and config["photo_count"] > 0:
                activities.append(config)

    if verbose:
        print("", file=sys.stderr)

    return sorted(activities, key=lambda x: -x["photo_count"])


def find_activity_by_keyword(keyword: str, activities: list[dict] = None) -> Optional[dict]:
    """根據關鍵字找活動"""
    if activities is None:
        activities = scan_activities(verbose=True)

    keyword_variants = normalize_keyword(keyword.lower())

    for act in activities:
        title_lower = act["title"].lower()
        for kw in keyword_variants:
            if kw in title_lower:
                return act

    return None


def search_by_bib(activity_id: int, bib_number: str, event_name: str = None) -> dict:
    """用號碼布搜尋照片"""
    search_url = f"{BASE_URL}/albumsearch/{activity_id}?code={bib_number}"

    # 如果沒有活動名稱，嘗試從 API 取得
    if not event_name:
        config = get_activity_config(activity_id)
        if config:
            event_name = config.get("title")

    return {
        "bib_number": bib_number,
        "activity_id": activity_id,
        "search_url": search_url,
        "event_name": event_name,
    }


def main():
    parser = argparse.ArgumentParser(
        description="捷安 (Soonnet) 馬拉松照片搜尋",
        epilog="""
範例:
  python soonnet_search.py -e "高雄" -b 12244     # 用關鍵字搜尋
  python soonnet_search.py -a 1376 -b 13213      # 用活動 ID 搜尋
  python soonnet_search.py -l                    # 列出有照片的活動
  python soonnet_search.py --scan                # 掃描所有有照片的活動
        """
    )
    parser.add_argument("--event", "-e", help="活動名稱關鍵字")
    parser.add_argument("--bib", "-b", help="號碼布號碼")
    parser.add_argument("--activity-id", "-a", type=int, help="活動 ID (直接指定)")
    parser.add_argument("--list-events", "-l", action="store_true", help="列出有照片的活動")
    parser.add_argument("--scan", action="store_true", help="掃描所有活動 (較慢)")
    parser.add_argument("--keyword", "-k", help="過濾活動關鍵字")
    parser.add_argument("--json", "-j", action="store_true", help="輸出 JSON 格式")

    args = parser.parse_args()

    # 掃描或列出活動模式
    if args.list_events or args.scan:
        activities = scan_activities(verbose=True)

        # 關鍵字過濾
        if args.keyword:
            keyword_variants = normalize_keyword(args.keyword.lower())
            activities = [
                a for a in activities
                if any(kw in a["title"].lower() for kw in keyword_variants)
            ]

        if args.json:
            print(json.dumps(activities, ensure_ascii=False, indent=2))
        else:
            print(f"\n=== 找到 {len(activities)} 個有照片的活動 ===\n")
            for act in activities:
                print(f"  ID: {act['id']:5} | 照片: {act['photo_count']:>7} | 攝影師: {act['photographers']:>2} | {act['title']}")
            print(f"\n使用方式: python soonnet_search.py -a <ID> -b <號碼布>")
        return

    # 搜尋模式
    if args.bib:
        activity_id = args.activity_id
        event_name = None

        # 用關鍵字找活動 ID
        if not activity_id and args.event:
            print(f"搜尋活動: {args.event}...", file=sys.stderr)
            act = find_activity_by_keyword(args.event)
            if act:
                activity_id = act["id"]
                event_name = act["title"]
                if not args.json:
                    print(f"找到活動: [{activity_id}] {event_name}")
            else:
                print(f"Error: 找不到符合 '{args.event}' 的活動", file=sys.stderr)
                print("提示: 使用 -l 列出所有有照片的活動", file=sys.stderr)
                sys.exit(1)

        if not activity_id:
            print("Error: 請提供 --event 或 --activity-id", file=sys.stderr)
            sys.exit(1)

        result = search_by_bib(activity_id, args.bib, event_name)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"搜尋結果")
            print(f"{'='*60}")
            print(f"網站: 捷安 Soonnet")
            print(f"活動: [{result['activity_id']}] {result.get('event_name', '未知')}")
            print(f"號碼布: {result['bib_number']}")
            print(f"{'='*60}")
            print(f"\n搜尋連結: {result['search_url']}")
            print(f"\n注意: 開啟連結後需等待約 10 秒載入")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
