# 好拍 GoodShot 網站結構

## 基本資訊

- **網站**: https://goodshot.com.tw
- **技術架構**: Vue.js SPA
- **API 格式**: RESTful JSON

## API 端點

### 1. 賽事列表

```
GET /api/front/v1/competition
```

回應:
```json
{
  "code": 200,
  "data": [
    {
      "id": 303,
      "title": "2026高雄富邦馬拉松",
      "county": "高雄國家體育場",
      "date": "2026-01-11T00:00:00+08:00",
      "photosNum": 85922,
      "photographersNum": 1
    }
  ]
}
```

### 2. 照片搜尋

```
GET /api/front/v1/competition/{competitionId}/photo/search
```

參數:
| 參數 | 類型 | 說明 |
|------|------|------|
| row | int | 每頁數量 |
| page | int | 頁碼 (從 0 開始) |
| bibNum | string | 號碼布號碼 |
| fuzzy | boolean | 模糊搜尋 |

回應:
```json
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": 9131885,
        "coverImg": "/assets/photo/303/21/xxx.jpeg",
        "bibNum": "32319",
        "bibNum1": "",
        "takeTime": "2026-01-11T07:37:40+08:00",
        "ownerName": "Mike"
      }
    ],
    "count": 19
  }
}
```

## URL 格式

- 照片: `https://goodshot.com.tw{coverImg}`
- 搜尋頁面: `https://goodshot.com.tw/findPhotos` (不支援 URL 參數預填)
- 賽事頁面: `https://goodshot.com.tw/competitions/{id}/competitionPG` (推薦使用)

## 特點

- 無需認證即可存取 API
- 每張照片最多辨識 9 個號碼布 (bibNum ~ bibNum8)
- 支援精確/模糊搜尋
