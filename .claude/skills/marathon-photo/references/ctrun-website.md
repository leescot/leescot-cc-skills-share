# 全統運動 CTRun 網站結構

## 基本資訊

- **網站**: https://www.ctrun.com.tw
- **照片下載**: https://www.ctrun.com.tw/album
- **技術架構**: ASP.NET MVC + HTML
- **照片存儲**: Azure Blob Storage (ctrunstorage.blob.core.windows.net)

## URL 模式

### 頁面 URL

```
賽事列表: https://www.ctrun.com.tw/album
關鍵字搜尋: https://www.ctrun.com.tw/Album/IndexSearch?Keyword={關鍵字}
賽事詳細: https://www.ctrun.com.tw/Album/detail?EventMain_ID={id}
號碼布搜尋: https://www.ctrun.com.tw/Album/NumPhotos?EventMain_ID={id}&Num={bib}
照片列表 (依類別): https://www.ctrun.com.tw/Album/Photos?EventMain_ID={id}&Category={category}
照片列表 (依時間): https://www.ctrun.com.tw/Album/Photos?EventMain_ID={id}&Category={category}&TimeFlag={time}
```

### 照片 URL

```
https://ctrunstorage.blob.core.windows.net/album/{event_code}/{category}/{filename}.jpg
```

參數說明:
- `event_code`: 賽事代碼 (例: NH251214)
- `category`: 相簿類別 (例: 1_活動紀錄)
- `filename`: 照片檔名

## HTML 解析

### 賽事列表

```html
<a href="/Album/detail?EventMain_ID=231">
  <img src="...">
</a>
<h5>2025</h5>
<h6>屏東馬拉松</h6>
```

### 搜尋結果

照片以連結形式顯示，直接連結到 Azure Blob Storage：

```html
<a href="https://ctrunstorage.blob.core.windows.net/album/NH251214/1_活動紀錄/AND_3403.jpg">
  <img src="..." alt="1_活動紀錄">
</a>
```

## 特點

- 無需登入即可搜尋和查看照片
- 照片存放在 Azure Blob Storage，URL 直接可存取
- 高號碼布標記率 (99%+)
- 照片無浮水印
- 支援號碼布、地點、時間搜尋
