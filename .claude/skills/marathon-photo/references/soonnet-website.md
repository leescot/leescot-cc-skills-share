# 捷安 (Soonnet) 網站結構

## 基本資訊

- **網站**: https://www.soonnetmall.com
- **技術架構**: Vue.js SPA + RESTful API (需認證)
- **公司**: 捷安網路科技股份有限公司
- **統編**: 54361108
- **聯絡信箱**: service@soonnetmall.com
- **Facebook**: https://www.facebook.com/profile.php?id=61565238743357
- **Instagram**: https://www.instagram.com/soonnetmall/

## URL 模式

### 頁面 URL

```
首頁: https://www.soonnetmall.com/index
活動列表 (未來活動): https://www.soonnetmall.com/eventlist
活動詳情 (未來活動): https://www.soonnetmall.com/eventdetails/{event_id}
活動照片列表: https://www.soonnetmall.com/activityevent/{activity_id}
照片搜尋結果: https://www.soonnetmall.com/albumsearch/{activity_id}?code={bib}
攝影師相簿: https://www.soonnetmall.com/albumphotodetail/{album_id}
```

### API 端點

```
API 基礎 URL: https://apimall.soonnetmall.com/api/services/app

可用 (無需認證):
  活動設定: GET /Activity/GetConfigByActivityId?activityId={id}
  活動基本資訊: GET /Activity/Get?id={id}
  未來活動列表: POST /Activity/GetAll

需認證 (無法使用):
  活動列表: POST /Activity/GetIndex
  照片搜尋: POST /PhotoGalleryConfigAppSerivce/GetPhotoGalleryListNew
```

**GetConfigByActivityId 回應範例**:
```json
{
  "success": true,
  "result": {
    "id": 1376,
    "title": "2025 臺北馬拉松",
    "sheyinCount": 15,
    "list": [
      {"coId": 2618, "photoCount": 59585, "image": "..."}
    ]
  }
}
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| activity_id | 活動 ID (有照片的活動) | 1376 |
| event_id | 賽事 ID (未來活動) | 2652 |
| album_id | 攝影師相簿 ID | 2618 |
| code | 號碼布號碼 | 13213 |

## 已知活動 ID

| 活動名稱 | Activity ID | 日期 |
|----------|-------------|------|
| 2025 臺北馬拉松 | 1376 | 2025-12-21 |
| 2026 高雄富邦馬拉松 | 2765 | 2026-01-11 |

**注意**: 活動 ID 可從首頁下拉選單獲取，選擇活動後 URL 會顯示 `/activityevent/{activity_id}`

## 搜尋流程

### 手動搜尋步驟

1. 進入首頁 https://www.soonnetmall.com
2. 點擊下拉選單「請選擇活動」
3. 選擇目標活動
4. 在「搜尋號碼布」輸入框輸入號碼
5. 點擊搜尋按鈕
6. **等待約 10 秒載入**
7. 查看搜尋結果

### 直連搜尋 URL

```
https://www.soonnetmall.com/albumsearch/{activity_id}?code={bib}
```

範例:
```
https://www.soonnetmall.com/albumsearch/1376?code=13213
```

## 技術特點

1. **Vue.js SPA**: 網站使用 Vue.js 單頁應用程式，需要 JavaScript 渲染
2. **API 認證**: API 需要特殊認證，無法直接呼叫
3. **慢速載入**: 搜尋結果需要等待約 10 秒載入
4. **臉部搜尋**: 支援臉部辨識搜尋功能
5. **前後五秒**: 提供「前後五秒」按鈕查看相近時間的照片
6. **攝影師分類**: 依攝影師分類照片

## 照片價格

- 單張價格: NT$169 - NT$189
- 價格依攝影師可能有所不同

## 首頁下拉選單資訊

下拉選單顯示以下欄位:
- 日期 (YYYY-MM-DD)
- 活動名稱
- 照片張數
- 攝影師人數
- 地區

範例:
```
2025-12-21 | 2025 臺北馬拉松 | 475472張 | 15位 | 臺北市
```

## 台/臺 字元說明

此網站使用「臺」(傳統正體) 而非「台」:
- 「臺北馬拉松」(正確)
- 「台北馬拉松」(可能搜尋不到)

搜尋時建議使用「臺」或同時嘗試兩種寫法。

## 與其他平台比較

| 特性 | 捷安 Soonnet | ZSport | AllSports |
|------|--------------|--------|-----------|
| 技術架構 | Vue.js SPA | SSR + REST API | PHP + AJAX |
| API 存取 | 需認證 | 公開 | 公開 |
| URL 直連搜尋 | 支援 | 不支援 | 支援 |
| 需登入 | 否 | 否 | 否 |
| 自動化難度 | 困難 | 容易 | 中等 |
| 載入速度 | 慢 (~10秒) | 快 | 中等 |

## 自動化注意事項

1. **SPA 架構**: 無法使用純 requests 庫，需要 Playwright/Selenium
2. **等待載入**: 搜尋結果需等待約 10 秒
3. **活動列表**: 需從首頁下拉選單獲取，eventlist 頁面為未來活動
4. **API 認證**: 直接呼叫 API 會失敗
5. **建議方式**: 使用 URL 直連搜尋，配合已知活動 ID 對照表
