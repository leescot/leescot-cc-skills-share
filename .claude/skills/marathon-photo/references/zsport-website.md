# ZSport 網站結構

## 基本資訊

- **網站**: https://www.zsport.com.tw
- **技術架構**: Server-side rendered HTML + RESTful JSON API
- **聯絡信箱**: zsportadm@gmail.com
- **Line**: @687wlazu

## URL 模式

### 頁面 URL

```
首頁 (賽事列表): https://www.zsport.com.tw/
活動頁面: https://www.zsport.com.tw/activity/{activity_id}
購物車: https://www.zsport.com.tw/order/view
```

### API 端點

```
照片搜尋: GET /api/activity/{activity_id}?page={page}&q={bib}
攝影師列表: GET /api/author/list?act_id={activity_id}
購物車: GET /cart/get
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| activity_id | 活動 ID | 254 |
| page | 頁碼 (從 1 開始) | 1 |
| q | 號碼布搜尋 | 32319 |

## API 回應格式

### 照片搜尋 API

```json
{
  "ver": "1.0",
  "rtncode": 0,
  "errcause": "",
  "result": "ok",
  "data": {
    "id": 254,
    "name": "2026 高雄富邦馬拉松-Day2",
    "action_time": "2026-01-11 00:00:00",
    "status": 1,
    "page": 1,
    "qstr": "32319",
    "photo": {
      "current_page": 1,
      "total": 21,
      "per_page": 49,
      "from": 1,
      "to": 21,
      "data": [
        {
          "id": 19576848,
          "sha1": "abc123...",
          "actid": 254,
          "price": 168,
          "author_id": 11,
          "shoot_time": "2026-01-11 07:30:00",
          "author_name": "小得哥",
          "best": 0
        }
      ]
    }
  }
}
```

### 回應欄位說明

| 欄位 | 說明 |
|------|------|
| rtncode | 0=成功, 其他=錯誤 |
| data.name | 活動名稱 |
| data.action_time | 活動日期 |
| photo.total | 照片總數 |
| photo.data[].id | 照片 ID |
| photo.data[].sha1 | 照片 hash (用於 URL) |
| photo.data[].price | 單張價格 (元) |
| photo.data[].shoot_time | 拍攝時間 |
| photo.data[].author_name | 攝影師名稱 |

## 照片 URL 格式

```
縮圖: https://www.zsport.com.tw/img/photo/{activity_id}/{sha1}_s.webp
```

## HTML 解析 (首頁活動列表)

```html
<table>
  <tr>
    <td>
      <a href="/activity/254">2026 高雄富邦馬拉松-Day2</a>
      <div>180,414張</div>
    </td>
  </tr>
</table>
```

### 活動資訊提取

- 活動連結: `/activity/{id}` 格式
- 照片數量: 含有 `{數字}張` 的文字
- 剩餘天數: `(剩{N}天)` 格式 (表示販售即將結束)

## 特點

1. **RESTful API**: 使用標準 JSON API 搜尋照片
2. **無需登入**: 號碼布搜尋免登入
3. **單張購買**: 每張 168 元
4. **35 天販售期**: 賽事照片只販售 35 天
5. **攝影師分類**: 可依攝影師篩選照片
6. **時間篩選**: 支援依拍攝時間範圍篩選

## 與其他平台比較

| 特性 | ZSport | AllSports | 好拍 GoodShot |
|------|--------|-----------|---------------|
| 技術架構 | SSR + REST API | PHP + AJAX | Vue.js SPA |
| URL 直連搜尋 | 不支援 | 支援 | 不支援 |
| 照片存儲 | 自有伺服器 | CloudFront | 自有伺服器 |
| 付費模式 | 單張 168 元 | 套餐 990 元 | 單張/套餐 |
| 需登入 | 否 | 否 | 否 |
| API 難度 | 容易 | 中等 | 容易 |

## 自動化注意事項

1. **活動列表**: 從首頁 HTML 解析，無專用 API
2. **照片搜尋**: 使用 `/api/activity/{id}?q={bib}` API
3. **分頁處理**: 每頁最多 49 張照片
4. **錯誤處理**: 檢查 `rtncode` 是否為 0
5. **URL 不支援參數**: 搜尋頁面無法用 URL 參數預填號碼布
