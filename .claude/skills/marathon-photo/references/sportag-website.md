# 運動標籤 Sportag 網站結構

## 基本資訊

- **網站**: https://www.sportag.net
- **技術架構**: 傳統 PHP + HTML
- **照片存儲**: 阿里雲 OSS (photos.sportag.net)

## URL 模式

### 頁面 URL

```
賽事列表: https://www.sportag.net/web/event.php
賽事頁面: https://www.sportag.net/web/event-photo.php?event_id={id}&view=all
號碼布搜尋: https://www.sportag.net/web/event-photo.php?event_id={id}&code={bib}
```

### 照片 URL

```
https://photos.sportag.net/{event_id}/{filename}.jpg?x-oss-process=style%2Fwatermark-sportag-line-v&OSSAccessKeyId=...&Expires=...&Signature=...
```

參數說明:
- `x-oss-process`: 圖片處理 (浮水印)
- `OSSAccessKeyId`: 阿里雲 OSS Access Key
- `Expires`: 簽名過期時間
- `Signature`: 簽名

## HTML 解析

### 賽事列表

```html
<a href="event-photo.php?event_id=1215&view=all">
  <img src="...">
  <p>2026 高雄富邦馬拉松 2026-01-11</p>
</a>
```

### 搜尋結果

照片以卡片形式顯示，包含:
- Photo ID
- 拍攝時間
- 縮圖 (帶浮水印)

## 特點

- 無 REST API，需解析 HTML
- 照片 URL 有時效簽名
- 支援號碼布精確搜尋
- 照片有「DO NOT COPY」浮水印
