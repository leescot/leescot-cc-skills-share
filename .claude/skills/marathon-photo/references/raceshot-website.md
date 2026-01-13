# RaceShot 運動拍檔 網站結構

## 網站資訊

- **網站名稱**: 運動拍檔 RaceShot
- **網址**: https://raceshot.app/
- **API 基礎 URL**: https://api.raceshot.app/api/v1/public/
- **公司**: 人生拾光有限公司 (統編: 60593621)

## API 端點

### 1. 活動列表 API

```
GET https://api.raceshot.app/api/v1/public/events
```

**Query Parameters:**

| 參數 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `search` | string | 搜尋關鍵字 (需 URL encode) | `%E5%8F%B0%E5%8C%97%E9%A6%AC` |
| `month` | string | 篩選月份 | `2025/12` |
| `location` | string | 篩選地點 | `臺北市` |
| `page` | int | 頁碼 (從 1 開始) | `1` |
| `limit` | int | 每頁筆數 | `10` |
| `sortOrder` | string | 排序方式 | `DESC` or `ASC` |
| `minPublishedPhotos` | string | 最少照片數 | `1` |

**Response 結構:**

```json
{
  "events": [
    {
      "id": "251203",
      "date": "2025/12/21",
      "name": "2025 台北馬拉松（正式賽）",
      "location": "臺北市",
      "categories": ["馬拉松"],
      "description": "...",
      "url": "https://...",
      "address": "...",
      "organizer": "...",
      "venue": "...",
      "sales_end_date": "2026-01-20T00:00:00.000Z",
      "published_photo_count": 43156
    }
  ],
  "total": 139,
  "page": 1,
  "limit": 10,
  "filters": {
    "month": "",
    "location": "",
    "search": "",
    ...
  }
}
```

### 2. 照片 API

```
GET https://api.raceshot.app/api/v1/public/photos?eventId={event_id}
```

**Query Parameters:**

| 參數 | 類型 | 說明 | 必填 |
|------|------|------|------|
| `eventId` | string | 活動 ID | 是 |

**注意**: `bib` 參數在 URL 中無效，號碼布篩選需在 client-side 進行。

**Response 結構:**

```json
{
  "eventId": "251203",
  "photos": [
    {
      "photo_id": "photo_1766304489263_1880",
      "event_id": "251203",
      "photographer_id": 20,
      "photographer_name": "運動拍檔",
      "price": 169,
      "create_date": "2025-12-21 08:05:20",
      "capture_timestamp": 1766272997000,
      "bib_number": "[\"024\", \"03342\", \"13213\", ...]",
      "location": "樂群一路（下塔悠公園天橋）",
      "uploaded_at": "2025-12-21 00:45:35"
    }
  ]
}
```

**bib_number 欄位格式:**
- JSON 字串陣列，例如: `"[\"13213\", \"12345\"]"`
- 特殊值 `"[\"x\"]"` 表示無法辨識號碼布
- 需 parse JSON 後進行比對

## 照片 URL 格式

照片縮圖和原圖 URL 需透過前端計算，基於 `photo_id` 組成。

## 網頁結構

### 活動列表頁

```
https://raceshot.app/events
```

- 顯示所有活動
- 支援時間和地點篩選
- 分頁顯示

### 活動照片頁

```
https://raceshot.app/events/{event_id}
```

- 動態載入照片
- 號碼布搜尋 (spinbutton 輸入)
- 支援時間、地點、攝影師篩選
- AI 屬性找照片功能

## 搜尋邏輯

1. **活動搜尋**: 使用 API `search` 參數
2. **號碼布搜尋**:
   - API 回傳所有照片
   - Client-side 篩選 `bib_number` 欄位
   - 支援部分比對 (輸入 "13213" 會匹配包含此號碼的照片)

## 價格

- 單張照片: NT$169

## 測試結果

**測試條件**: 2025 台北馬拉松, 號碼布 13213

| 項目 | 結果 |
|------|------|
| Event ID | 251203 |
| 總照片數 | 43,156 張 |
| 匹配號碼布 13213 | **15 張** |
| 拍攝地點 | 樂群一路（下塔悠公園天橋） |

## 注意事項

1. **API 效能**: 照片 API 回傳全部照片，大型活動可能有數萬張，回應可達數 MB
2. **Client-side 篩選**: 號碼布篩選需在本地進行，API 不支援
3. **URL Encoding**: 中文搜尋關鍵字需 URL encode
4. **銷售期限**: 照片有銷售期限，過期後可能無法購買
