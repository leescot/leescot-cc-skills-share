# AllSports 網站結構

## 基本資訊

- **網站**: https://allsports.tw
- **技術架構**: 傳統 PHP + HTML
- **營運公司**: 創星影像股份有限公司 (日本 PhotoCreate 台灣分公司)
- **聯絡信箱**: allsports@photocreate.com.tw

## URL 模式

### 頁面 URL

```
首頁 (賽事列表): https://allsports.tw/
賽事頁面: https://allsports.tw/event/{event_code}.html
號碼布搜尋結果: https://allsports.tw/view/{event_id}/{event_id}/zekken/{bib}/
相簿頁面: https://allsports.tw/view/{event_id}/{event_id}/album/{album_id}/
購物車: https://allsports.tw/cart/cart.php
套餐購買: https://allsports.tw/cart/alldata.php?pid={event_id}&zekken={bib}
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| event_code | 8 位數賽事代碼 (含前導零) | 00778854 |
| event_id | 賽事 ID (數字) | 778854 |
| bib | 號碼布號碼 | 32319 |
| album_id | 相簿 ID | 12280188 |

## HTML 解析

### 首頁賽事列表

```html
<table>
  <tr>
    <td>
      <a href="/event/00778854.html">2026-01-11 2026 高雄富邦馬拉松</a>
    </td>
  </tr>
</table>
```

### 搜尋結果頁面

```html
<h1>號碼布編號：32319（共26張）</h1>

<li>
  <p>NO: 3573-2832947</p>
  <p>TIME: 06:42</p>
  <img src="/photo/thumbnail.jpg">
</li>
```

## 特點

1. **URL 支援直接搜尋**: 可直接構建搜尋結果 URL
2. **無需登入**: 號碼布搜尋免登入
3. **付費下載**: 套餐 990 元（所有照片電子檔）
4. **照片有時間戳**: 可看到拍攝時間
5. **多拍攝點**: 依地點分類照片
6. **優惠期限**: 賽後有限時優惠

## 與其他平台比較

| 特性 | AllSports | 好拍 GoodShot | Phomi 瘋迷 |
|------|-----------|---------------|------------|
| 技術架構 | PHP + HTML | Vue.js SPA | PHP + AJAX |
| URL 直連搜尋 | 支援 | 不支援 | 支援 |
| 照片存儲 | 自有伺服器 | 自有伺服器 | 自有伺服器 |
| 付費模式 | 套餐 990 元 | 單張/套餐 | 單張/套餐 |
| 需登入 | 否 | 否 | 否 |
| 自動化難度 | 容易 | 容易 | 中等 |

## 自動化注意事項

1. **URL 直接搜尋**: 可直接構建 `/view/{id}/{id}/zekken/{bib}/` URL
2. **賽事代碼**: 賽事頁面需要 8 位數代碼，搜尋 URL 用數字 ID
3. **HTML 解析**: 需解析 HTML 取得照片數量和列表
4. **照片數量**: 從 `<h1>` 標題中的「共N張」解析
