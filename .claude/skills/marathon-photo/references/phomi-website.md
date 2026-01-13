# Phomi 瘋迷網站技術參考

## 網站概述

- **網站名稱**: Phomi 瘋迷
- **網址**: http://www.phomi.com.tw/
- **功能**: 台灣馬拉松賽事照片搜尋與購買平台

## URL 結構

### 主要頁面

| 頁面 | URL | 說明 |
|-----|-----|------|
| 首頁 | `/index.php` | 網站入口 |
| 活動列表 | `/activity-list.php` | 相簿找照片入口 |
| 活動照片 | `/activity-photo.php?ActCode={code}` | 特定活動頁面 |
| 號碼布搜尋結果 | `/bib-found-photo.php?bibtxt={bib}&ActCode={code}` | 搜尋結果 |
| 更多可能照片 | `/bib-found-photo-more.php?bibtxt={bib}&ActCode={code}` | 模糊匹配 |

### URL 參數

| 參數 | 說明 | 範例 |
|-----|------|------|
| `ActCode` | 活動代碼 (8位數字) | `83058571` |
| `bibtxt` | 號碼布號碼 | `32319` |
| `Aid` | 攝影師 ID | `19791` |

## HTML 結構

### 活動列表頁面 (activity-list.php)

活動表格結構：
```html
<table>
  <tr>
    <td>日期</td>
    <td><a href="activity-photo.php?ActCode=XXXXXXXX">活動名稱</a></td>
    <td>城市</td>
    <td>攝影師數</td>
    <td>照片數</td>
    <td>典藏狀態</td>
  </tr>
</table>
```

### 搜尋結果頁面 (bib-found-photo.php)

關鍵文字模式：
- 標題: `{號碼布}號碼布 - {活動名稱}`
- 精確匹配: `找到{號碼布}號碼布照片{N}張`
- 更多照片連結: `更多...可能是{號碼布}號的相片，{N}張`

## 測試案例

### 高雄馬拉松 + 號碼布 32319

```
活動名稱: 2026高雄富邦馬拉松 第二天
活動代碼: 83058571
搜尋 URL: http://www.phomi.com.tw/bib-found-photo.php?bibtxt=32319&ActCode=83058571
精確匹配: 9 張
可能相關: 92 張
```

## 注意事項

1. 網站使用 UTF-8 編碼
2. 部分活動分多天舉行 (如「第一天」「第二天」)
3. 照片數量較多的場次通常為主賽日
4. 網站無明顯的反爬蟲機制，但建議加入適當延遲
