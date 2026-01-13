#!/usr/bin/env python3
"""
尋寶網 (Soonnet.org) 馬拉松照片搜尋腳本

使用方式:
    python soonnet_org_search.py -e "麗晨台中" -b 11513   # 搜尋相簿並提供連結
    python soonnet_org_search.py -l -k "馬拉松"           # 列出馬拉松相關相簿
    python soonnet_org_search.py -i 183648 -b 11513       # 直接用相簿 ID

特點:
    - 尋寶網照片免費下載
    - 同一賽事照片分散在不同攝影師相簿中
    - API 不支援號碼布搜尋，需手動在相簿中搜尋

API 端點:
    - GetAll: 取得相簿列表 (支援關鍵字過濾)
    - GetPhotoGalleryList: 取得相簿照片 (不支援號碼布搜尋)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Optional

BASE_URL = "https://www.soonnet.org"
API_URL = "https://api.soonnet.org/api/services/app"

# 台/臺 轉換表
TAIWAN_CHAR_MAP = {
    '台': '臺',
    '臺': '台',
}

# 分類 ID
CATEGORY_RUNNING = 10217  # 路跑


def normalize_keyword(keyword: str) -> list[str]:
    """產生關鍵字的變體 (處理 台/臺 轉換)"""
    variants = [keyword]
    for char, replacement in TAIWAN_CHAR_MAP.items():
        if char in keyword:
            variant = keyword.replace(char, replacement)
            if variant not in variants:
                variants.append(variant)
    return variants


def api_post(endpoint: str, data: dict) -> Optional[dict]:
    """呼叫 POST API"""
    url = f"{API_URL}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json",
    }

    json_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success", True):
                return result.get("result")
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"API 錯誤: {e}", file=sys.stderr)
    return None


def search_albums(keyword: str = None, category: int = CATEGORY_RUNNING,
                  max_results: int = 100) -> list[dict]:
    """搜尋相簿列表"""
    data = {
        "SGL_PG_CMasterSort": category,
        "MaxResultCount": max_results,
        "SkipCount": 0,
    }

    result = api_post("/PhotoGalleryConfigAppSerivce/GetAll", data)
    if not result:
        return []

    albums = result.get("items", [])

    # 關鍵字過濾
    if keyword:
        keyword_variants = normalize_keyword(keyword.lower())
        filtered = []
        for album in albums:
            title = album.get("sgL_PG_CName", "").lower()
            if any(kw in title for kw in keyword_variants):
                filtered.append(album)
        albums = filtered

    return albums


def get_album_info(album_id: int) -> Optional[dict]:
    """取得相簿資訊"""
    data = {
        "id": album_id,
        "MaxResultCount": 1,
        "SkipCount": 0,
    }

    result = api_post("/PhotoGalleryConfigAppSerivce/GetPhotoGalleryList", data)
    if result:
        return {
            "id": album_id,
            "title": result.get("sgL_PG_CName"),
            "photographer": result.get("sgL_Mem_DisplayName"),
            "photo_count": result.get("sgL_PG_CPhotoQuantity", 0),
            "identified": result.get("isAuth", 0),
            "unidentified": result.get("isNotAuth", 0),
            "date": result.get("sgL_PG_CShootTimerF"),
        }
    return None


def format_album(album: dict) -> dict:
    """格式化相簿資訊"""
    album_id = album.get("id")
    return {
        "id": album_id,
        "title": album.get("sgL_PG_CName"),
        "photographer": album.get("sgL_Mem_DisplayName"),
        "photo_count": album.get("sgL_PG_CPhotoQuantity", 0),
        "date": album.get("sgL_PG_CAddTimerF"),
        "url": f"{BASE_URL}/albumviewPhotostream?id={album_id}",
        "short_url": f"{BASE_URL}/D{album_id}",
    }


def search_by_event(event_keyword: str, bib_number: str = None) -> list[dict]:
    """根據賽事關鍵字搜尋相簿"""
    albums = search_albums(keyword=event_keyword)

    results = []
    for album in albums:
        info = format_album(album)
        if bib_number:
            # 提示用戶需要手動搜尋號碼布
            info["bib_search_note"] = f"請在相簿中手動搜尋號碼布: {bib_number}"
        results.append(info)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="尋寶網 (Soonnet.org) 馬拉松照片搜尋",
        epilog="""
範例:
  python soonnet_org_search.py -e "麗晨台中" -b 11513   # 搜尋麗晨台中馬相簿
  python soonnet_org_search.py -l -k "馬拉松"           # 列出馬拉松相簿
  python soonnet_org_search.py -i 183648                # 查看特定相簿

注意:
  - 尋寶網照片免費下載
  - 同一賽事照片分散在不同攝影師相簿中
  - 需在各相簿中手動搜尋號碼布
        """
    )
    parser.add_argument("--event", "-e", help="賽事名稱關鍵字")
    parser.add_argument("--bib", "-b", help="號碼布號碼 (僅供參考)")
    parser.add_argument("--album-id", "-i", type=int, help="相簿 ID (直接指定)")
    parser.add_argument("--list-albums", "-l", action="store_true", help="列出相簿")
    parser.add_argument("--keyword", "-k", help="過濾關鍵字")
    parser.add_argument("--limit", "-n", type=int, default=20, help="最大結果數 (預設 20)")
    parser.add_argument("--json", "-j", action="store_true", help="輸出 JSON 格式")

    args = parser.parse_args()

    # 列出相簿模式
    if args.list_albums:
        albums = search_albums(keyword=args.keyword, max_results=args.limit)

        if args.json:
            print(json.dumps([format_album(a) for a in albums], ensure_ascii=False, indent=2))
        else:
            print(f"\n=== 找到 {len(albums)} 個相簿 ===\n")
            for album in albums:
                info = format_album(album)
                print(f"  ID: {info['id']:6} | 照片: {info['photo_count']:>6} | {info['photographer'][:10]:10} | {info['title']}")
            print(f"\n使用方式: python soonnet_org_search.py -i <ID>")
            print(f"提示: 需在相簿中手動搜尋號碼布")
        return

    # 查看特定相簿
    if args.album_id:
        info = get_album_info(args.album_id)
        if info:
            info["url"] = f"{BASE_URL}/albumviewPhotostream?id={args.album_id}"
            info["short_url"] = f"{BASE_URL}/D{args.album_id}"
            if args.bib:
                info["bib_search_note"] = f"請在相簿中手動搜尋號碼布: {args.bib}"

            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                print(f"\n{'='*60}")
                print(f"相簿資訊")
                print(f"{'='*60}")
                print(f"網站: 尋寶網 Soonnet.org (免費下載)")
                print(f"相簿: [{info['id']}] {info['title']}")
                print(f"攝影師: {info['photographer']}")
                print(f"照片數: {info['photo_count']} 張 (已識別: {info['identified']})")
                print(f"日期: {info['date']}")
                print(f"{'='*60}")
                print(f"\n相簿連結: {info['url']}")
                if args.bib:
                    print(f"\n請在相簿中手動搜尋號碼布: {args.bib}")
        else:
            print(f"Error: 找不到相簿 ID {args.album_id}", file=sys.stderr)
            sys.exit(1)
        return

    # 搜尋模式
    if args.event:
        print(f"搜尋相簿: {args.event}...", file=sys.stderr)
        results = search_by_event(args.event, args.bib)

        if not results:
            print(f"Error: 找不到符合 '{args.event}' 的相簿", file=sys.stderr)
            print(f"提示: 使用 -l -k \"馬拉松\" 列出所有相簿", file=sys.stderr)
            sys.exit(1)

        # 限制結果數
        results = results[:args.limit]

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"搜尋結果 - 找到 {len(results)} 個相簿")
            print(f"{'='*60}")
            print(f"網站: 尋寶網 Soonnet.org (免費下載)")
            print(f"關鍵字: {args.event}")
            if args.bib:
                print(f"號碼布: {args.bib}")
            print(f"{'='*60}")

            for i, album in enumerate(results, 1):
                print(f"\n[{i}] {album['title']}")
                print(f"    攝影師: {album['photographer']}")
                print(f"    照片數: {album['photo_count']} 張")
                print(f"    連結: {album['url']}")

            print(f"\n{'='*60}")
            print(f"注意: 需在各相簿中手動搜尋號碼布")
            if args.bib:
                print(f"搜尋號碼布: {args.bib}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
