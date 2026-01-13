# 尋寶網 (Soonnet.org) 網站結構

## 基本資訊

- **網站**: https://www.soonnet.org
- **技術架構**: Vue.js SPA + RESTful API
- **特色**: 照片免費下載、社群分享平台
- **聯絡方式**: info@soonnet.org

## 與其他平台差異

**重要**: 尋寶網與其他馬拉松照片平台不同：
1. **照片免費下載** (高清壓縮/原始無損)
2. **攝影師個人相簿制** - 同一賽事照片分散在不同攝影師相簿中
3. **無統一賽事搜尋** - 需逐一瀏覽相關相簿搜尋號碼布

## URL 模式

### 頁面 URL

```
首頁: https://www.soonnet.org/
相簿列表: https://www.soonnet.org/albumList?SGL_PG_CMasterSort=10217&currentPage=1&currentSize=60
相簿頁面: https://www.soonnet.org/albumviewPhotostream?id={album_id}
相簿短連結: https://www.soonnet.org/D{album_id}
照片頁面: https://www.soonnet.org/photoview?Coid={album_id}&Liid={photo_id}
攝影師頁面: https://www.soonnet.org/customerPublishLook?authorName={name}&authorId={id}
```

### API 端點

```
API 基礎 URL: https://api.soonnet.org/api/services/app

相簿列表:
  POST /PhotoGalleryConfigAppSerivce/GetAll
  Body: {"SGL_PG_CMasterSort": 10217, "MaxResultCount": 50, "SkipCount": 0}

相簿照片:
  POST /PhotoGalleryConfigAppSerivce/GetPhotoGalleryList
  Body: {"id": {album_id}, "MaxResultCount": 50, "SkipCount": 0}
```

**注意**: API 不支援號碼布搜尋，需在網頁上手動搜尋。

### 分類 ID (SGL_PG_CMasterSort)

| 分類 | ID |
|------|-----|
| 路跑 | 10217 |
| 單車 | (其他) |
| 鐵人 | (其他) |

### 照片 URL 格式

```
縮圖: https://twphoto.soonnet.org/Photo/Photo_Resources/{user_id}/{folder}/{photo_name}_S.jpg
預覽: https://twphoto.soonnet.org/Photo/Photo_Resources/{user_id}/{folder}/{photo_name}_P.jpg
下載 (壓縮): https://api.soonnet.org/Home/DownLoadImage?...&LokDLY=1&LokDLT=s
下載 (原始): https://api.soonnet.org/Home/DownLoadImage?...&LokDLY=2&LokDLT=l
```

## API 回應格式

### 相簿列表 GetAll 回應

```json
{
  "result": {
    "totalCount": 14280,
    "items": [
      {
        "id": 183648,
        "sgL_PG_CName": "2026 麗晨臺中國際馬拉松(09:00後）",
        "sgL_Mem_DisplayName": "568",
        "sgL_PG_CPhotoQuantity": 13830,
        "sgL_PG_CAddTimerF": "2026-01-12 09:28",
        "sgL_PG_CMasterSort": 10217,
        "sgL_PG_CMasterSortName": "路跑"
      }
    ]
  }
}
```

### 相簿詳情 GetPhotoGalleryList 回應

```json
{
  "result": {
    "id": 183648,
    "sgL_PG_CName": "2026 麗晨臺中國際馬拉松(09:00後）",
    "sgL_Mem_DisplayName": "568",
    "sgL_PG_CPhotoQuantity": 13830,
    "isAuth": 12545,
    "isNotAuth": 1285,
    "sgL_PG_CShootTimerF": "2026-01-11",
    "photoGalleryListDtl": {
      "totalCount": 13830,
      "items": [...]
    }
  }
}
```

### 欄位說明

| 欄位 | 說明 |
|------|------|
| id | 相簿 ID |
| sgL_PG_CName | 相簿名稱 |
| sgL_Mem_DisplayName | 攝影師名稱 |
| sgL_PG_CPhotoQuantity | 照片數量 |
| isAuth | 已識別照片數 |
| isNotAuth | 無法識別照片數 |
| sgL_PG_CAddTimerF | 上傳時間 |
| sgL_PG_CShootTimerF | 拍攝日期 |

## 搜尋流程

### 手動搜尋步驟

1. 進入相簿頁面 `https://www.soonnet.org/albumviewPhotostream?id={album_id}`
2. 在「號碼布搜尋」輸入框輸入號碼
3. 點擊搜尋圖標 (放大鏡)
4. 查看搜尋結果
5. 點擊「下載 (高清壓縮)」或「下載 (原始無損)」

### 搜尋功能說明

- **號碼布搜尋**: 在每個相簿中輸入號碼布搜尋
- **時間篩選**: 支援開始/結束時間篩選
- **排序**: 按最後更新/按熱門程度
- **臉部搜尋**: 支援上傳照片進行臉部辨識

## 測試結果

### 測試條件
- 賽事: 麗晨臺中國際馬拉松
- 號碼布: 11513

### 測試結果
- **相關相簿**: 6 個
  - 568 (09:00後): 13,830 張 (ID: 183648)
  - 568 (09:00前): 15,883 張 (ID: 183530)
  - 蘇老師: 8,128 張 (ID: 183579)
  - 秋水: 6,008 張 (ID: 183657)
  - Mango Pan: 3,831 張 (ID: 183526)
  - 林文平: 783 張 (ID: 183545)
- **總照片數**: 約 48,463 張
- **號碼布 11513 搜尋結果** (ID: 183648): 9 張

## 特色功能

### 免費下載
- 高清壓縮版: 壓縮後的照片
- 原始無損版: 原始檔案

### 號碼布識別
- 已識別: AI 識別出號碼布的照片
- 未識別: 尚未處理的照片
- 無法識別: 無法辨識號碼布的照片

### 社群功能
- 讚好、收藏、分享
- 留言功能
- 攝影師追蹤

## 台/臺 字元說明

此網站可能使用「臺」(傳統正體)：
- 「臺中國際馬拉松」(常見)
- 「台中國際馬拉松」(也可能出現)

搜尋腳本會自動處理兩種寫法。

## 與捷安 (Soonnet Mall) 比較

| 特性 | 尋寶網 Soonnet.org | 捷安 Soonnet Mall |
|------|-------------------|-------------------|
| 付費模式 | 免費下載 | 單張 169-189 元 |
| 組織方式 | 攝影師相簿 | 賽事統一 |
| 號碼布搜尋 | 各相簿分別搜尋 | 統一搜尋 |
| API 支援 | 相簿列表 API | 活動 API |
| 自動化難度 | 中等 | 容易 |

## 自動化注意事項

1. **API 限制**: 不支援號碼布搜尋，需網頁手動搜尋
2. **多相簿搜尋**: 同一賽事需搜尋多個攝影師相簿
3. **台/臺 轉換**: 需處理「台」和「臺」的轉換
4. **免費平台**: 無需付費即可下載

## 建議使用方式

1. 使用腳本搜尋相關相簿: `python soonnet_org_search.py -e "麗晨台中" -b 11513`
2. 依序開啟各相簿連結
3. 在每個相簿中搜尋號碼布
4. 免費下載需要的照片
