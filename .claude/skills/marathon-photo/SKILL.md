---
name: marathon-photo
description: This skill should be used when the user asks to "搜尋馬拉松照片", "找跑步照片", "search marathon photos", "find race photos", or mentions keywords like "號碼布", "bib number", "Phomi", "瘋迷", "好拍", "GoodShot", "運動標籤", "Sportag", "ZSport", "捷安", "Soonnet", "尋寶網", "RaceShot", "運動拍檔". Searches Taiwan marathon event photos by bib number on Phomi, GoodShot, Sportag, CTRun, AllSports, ZSport, Soonnet, Soonnet.org, and RaceShot websites.
---

# Marathon Photo Search

Search Taiwan marathon event photos by bib number using multiple platforms.

## Supported Platforms

| Platform | Script | Website |
|----------|--------|---------|
| **Phomi 瘋迷** | `phomi_search.py` | http://www.phomi.com.tw/ |
| **好拍 GoodShot** | `goodshot_search.py` | https://goodshot.com.tw/ |
| **運動標籤 Sportag** | `sportag_search.py` | https://www.sportag.net/ |
| **全統運動 CTRun** | `ctrun_search.py` | https://www.ctrun.com.tw/ |
| **AllSports** | `allsports_search.py` | https://allsports.tw/ |
| **ZSport** | `zsport_search.py` | https://www.zsport.com.tw/ |
| **捷安 Soonnet** | `soonnet_search.py` | https://www.soonnetmall.com/ |
| **尋寶網 Soonnet.org** | `soonnet_org_search.py` | https://www.soonnet.org/ |
| **運動拍檔 RaceShot** | `raceshot_search.py` | https://raceshot.app/ |

**注意**:
- **捷安 (Soonnet Mall)**: API 不支援號碼布搜尋，只能列出活動名稱和連結，**使用者需自行開啟連結搜尋號碼布**。
- **尋寶網 (Soonnet.org)**: API 不支援號碼布搜尋，只能列出相簿名稱和連結，**使用者需自行進入各相簿搜尋號碼布**。照片免費下載。

## Quick Start

### Search All Platforms

Execute all scripts to maximize photo coverage. **Use optimized short keywords (see Step 2):**

```bash
# Phomi (use short keyword: "高雄" instead of "高雄馬拉松")
python ${SKILL_DIR}/scripts/phomi_search.py --event "高雄" --bib 32319

# GoodShot
python ${SKILL_DIR}/scripts/goodshot_search.py --event "高雄" --bib 32319

# Sportag
python ${SKILL_DIR}/scripts/sportag_search.py --event "高雄" --bib 32319

# CTRun
python ${SKILL_DIR}/scripts/ctrun_search.py --event "高雄" --bib 32319

# AllSports
python ${SKILL_DIR}/scripts/allsports_search.py --event "高雄" --bib 32319

# ZSport
python ${SKILL_DIR}/scripts/zsport_search.py --event "高雄" --bib 32319

# Soonnet (需使用 activity-id，搜尋結果需等待載入)
python ${SKILL_DIR}/scripts/soonnet_search.py --activity-id 1376 --bib 13213

# Soonnet.org 尋寶網 (免費下載，需逐一搜尋各相簿)
python ${SKILL_DIR}/scripts/soonnet_org_search.py --event "高雄" --bib 32319

# RaceShot 運動拍檔
python ${SKILL_DIR}/scripts/raceshot_search.py --event "高雄" --bib 32319
```

## 台/臺 字元說明

**重要**: 台灣的「台」字有兩種寫法：
- 「台」: 常用簡寫
- 「臺」: 傳統正體

部分網站 (如**捷安 Soonnet**) 使用「臺」而非「台」，搜尋時需注意：

| 網站 | 使用字元 | 範例 |
|------|----------|------|
| 捷安 Soonnet | 臺 | 臺北馬拉松 |
| 其他平台 | 台/臺 皆可 | 台北馬拉松 |

**搜尋建議**:
1. 先嘗試「台」(如「台北」)
2. 若無結果，改用「臺」(如「臺北」)
3. 捷安腳本會自動嘗試兩種寫法

## Core Workflow

### Step 1: Identify Parameters

Extract from user request:
- **Event keyword**: Marathon name (e.g., "高雄馬拉松", "台北馬拉松")
- **Bib number**: Runner's race number (e.g., "32319")
- **Platform preference**: If user specifies a platform

### Step 2: Optimize Search Keyword

**IMPORTANT: Apply keyword optimization before searching**

1. **Extract short keyword (2 characters preferred)**
   - Use location/city name: "高雄", "台北", "屏東", "台中"
   - Or event brand name: "富邦", "渣打", "萬金石"

2. **Remove marathon suffixes first**
   - Remove: "馬拉松", "馬", "半馬", "全馬", "路跑", "超馬"
   - "高雄馬拉松" → "高雄"
   - "台北半馬" → "台北"
   - "屏東馬" → "屏東"

3. **Search strategy**
   ```
   Step A: Search with short keyword (e.g., "高雄")
   Step B: If no results, try original keyword (e.g., "高雄馬拉松")
   Step C: If still no results, try broader keyword (e.g., "馬拉松")
   ```

4. **Prefer recent events (within 60 days)**
   - When multiple events match, select the most recent one
   - Events from past 60 days are most likely to have photos uploaded

5. **處理多筆搜尋結果 - 詢問日期**
   - 當搜尋結果有多個不同日期的活動時，**詢問使用者要搜尋哪個日期**
   - 例如搜尋 "台北馬" 找到多筆結果，應詢問：
     ```
     找到多個符合「台北馬」的活動，請問是哪一天的？
     - 12/21 台北馬拉松（正式賽）
     - 12/20 臺北馬拉松（耶誕歡樂早餐跑）
     - 11/16 台北葡萄酒馬拉松
     ```
   - 使用者選定日期後，再進行搜尋

**Keyword Examples:**
| User Input | Optimized Keyword |
|------------|-------------------|
| 高雄馬拉松 | 高雄 |
| 台北半馬 | 台北 |
| 屏東馬 | 屏東 |
| 富邦馬拉松 | 富邦 |
| 渣打馬拉松 | 渣打 |
| 萬金石馬拉松 | 萬金石 |
| 田中馬 | 田中 |

### Step 3: Execute Search

**Default: Search all platforms** for maximum coverage.

### Step 4: Report Combined Results

**重要**: 輸出結果時請遵循以下規則：
1. **依照片數量排序**: 找到越多照片的平台排越前面
2. **分區顯示**: 可直接搜尋的平台放第一區，需手動搜尋的放第二區

```
## 搜尋結果

**活動**: {event_name}
**號碼布**: {bib_number}

---
### 🔍 搜尋結果 (依照片數量排序)

| 平台 | 照片數 | 連結 |
|------|--------|------|
| {平台名稱} | {N} 張 | [查看]({url}) |
| {平台名稱} | {M} 張 | [查看]({url}) |
| ... | ... | ... |

**小計**: {總數} 張

---
### 📂 需手動搜尋

以下平台 API 不支援號碼布搜尋，請自行前往搜尋：

| 平台 | 說明 | 連結 |
|------|------|------|
| 捷安 Soonnet | 需等待頁面載入後輸入號碼布 | [前往]({url}) |
| 尋寶網 Soonnet.org | 免費下載，需逐一進入相簿搜尋 | [前往]({url}) |

---
**總計**: {所有平台總數} 張 (不含手動搜尋平台)
```

**範例輸出** (假設搜尋結果):
```
## 搜尋結果

**活動**: 2025 台北馬拉松
**號碼布**: 13213

---
### 🔍 搜尋結果 (依照片數量排序)

| 平台 | 照片數 | 連結 |
|------|--------|------|
| 運動拍檔 RaceShot | 14 張 | [查看](https://raceshot.app/events/251203) |
| 好拍 GoodShot | 8 張 | [查看](https://goodshot.com.tw/...) |
| Phomi 瘋迷 | 5 張 | [查看](http://www.phomi.com.tw/...) |
| 運動標籤 Sportag | 3 張 | [查看](https://www.sportag.net/...) |

**小計**: 30 張

---
### 📂 需手動搜尋

| 平台 | 說明 | 連結 |
|------|------|------|
| 捷安 Soonnet | 需等待頁面載入後輸入號碼布 | [前往](https://www.soonnetmall.com/...) |
| 尋寶網 Soonnet.org | 免費下載，需逐一進入相簿搜尋 | [前往](https://www.soonnet.org/...) |

---
**總計**: 30 張
```

## Script Reference

### phomi_search.py

```bash
python scripts/phomi_search.py -e "活動關鍵字" -b 號碼布
python scripts/phomi_search.py -l -k "馬拉松"       # 列出活動
python scripts/phomi_search.py -a 83058571 -b 32319  # 用 ActCode
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--act-code, -a` | 活動代碼 |
| `--list-events, -l` | 列出活動 |
| `--json, -j` | JSON 輸出 |

### goodshot_search.py

```bash
python scripts/goodshot_search.py -e "活動關鍵字" -b 號碼布
python scripts/goodshot_search.py -l -k "馬拉松"  # 列出活動
python scripts/goodshot_search.py -c 303 -b 32319  # 用 competition ID
python scripts/goodshot_search.py -e "高雄馬拉松" -b 32319 -f  # 模糊搜尋
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--competition-id, -c` | 賽事 ID |
| `--fuzzy, -f` | 模糊搜尋 |
| `--list-events, -l` | 列出活動 |
| `--json, -j` | JSON 輸出 |

### sportag_search.py

```bash
python scripts/sportag_search.py -e "活動關鍵字" -b 號碼布
python scripts/sportag_search.py -l -k "馬拉松"  # 列出活動
python scripts/sportag_search.py -i 1215 -b 32319  # 用 event ID
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--event-id, -i` | 賽事 ID |
| `--list-events, -l` | 列出活動 |
| `--json, -j` | JSON 輸出 |

### ctrun_search.py

```bash
python scripts/ctrun_search.py -e "活動關鍵字" -b 號碼布
python scripts/ctrun_search.py -l -k "馬拉松"  # 列出活動
python scripts/ctrun_search.py -i 231 -b 50282  # 用 event ID
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--event-id, -i` | 賽事 ID |
| `--list-events, -l` | 列出活動 |
| `--keyword, -k` | 過濾關鍵字 |
| `--json, -j` | JSON 輸出 |

### allsports_search.py

```bash
python scripts/allsports_search.py -e "活動關鍵字" -b 號碼布
python scripts/allsports_search.py -l -k "馬拉松"  # 列出活動
python scripts/allsports_search.py -i 778854 -b 32319  # 用 event ID
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--event-id, -i` | 賽事 ID |
| `--list-events, -l` | 列出活動 |
| `--keyword, -k` | 過濾關鍵字 |
| `--json, -j` | JSON 輸出 |

### zsport_search.py

```bash
python scripts/zsport_search.py -e "活動關鍵字" -b 號碼布
python scripts/zsport_search.py -l -k "馬拉松"  # 列出活動
python scripts/zsport_search.py -a 254 -b 32319  # 用 activity ID
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--activity-id, -a` | 活動 ID |
| `--list-events, -l` | 列出活動 |
| `--keyword, -k` | 過濾關鍵字 |
| `--json, -j` | JSON 輸出 |

### soonnet_search.py

```bash
python scripts/soonnet_search.py -e "高雄" -b 12244    # 用關鍵字搜尋 (推薦)
python scripts/soonnet_search.py -a 1376 -b 13213     # 用 activity ID 搜尋
python scripts/soonnet_search.py -l                   # 列出有照片的活動
python scripts/soonnet_search.py -l -k "馬拉松"       # 過濾馬拉松活動
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 (會掃描 API 搜尋) |
| `--bib, -b` | 號碼布號碼 |
| `--activity-id, -a` | 活動 ID (直接指定) |
| `--list-events, -l` | 列出有照片的活動 (掃描 API) |
| `--keyword, -k` | 過濾關鍵字 |
| `--json, -j` | JSON 輸出 |

**API 端點** (無需開網頁):
- `GET /Activity/GetConfigByActivityId?activityId={id}` - 取得活動配置
- 腳本會掃描活動 ID 範圍，找出有照片的活動

**注意**: 搜尋結果頁面仍需等待約 10 秒載入。

### soonnet_org_search.py

```bash
python scripts/soonnet_org_search.py -e "麗晨台中" -b 11513  # 搜尋相簿並提供連結
python scripts/soonnet_org_search.py -l -k "馬拉松"          # 列出馬拉松相簿
python scripts/soonnet_org_search.py -i 183648               # 查看特定相簿
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 賽事名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 (僅供參考) |
| `--album-id, -i` | 相簿 ID (直接指定) |
| `--list-albums, -l` | 列出相簿 |
| `--keyword, -k` | 過濾關鍵字 |
| `--limit, -n` | 最大結果數 (預設 20) |
| `--json, -j` | JSON 輸出 |

**特點**:
- 照片免費下載 (高清壓縮/原始無損)
- 同一賽事照片分散在不同攝影師相簿中
- API 不支援號碼布搜尋，需在各相簿中手動搜尋

**注意**: 尋寶網與其他平台不同，需逐一進入相簿搜尋號碼布。

### raceshot_search.py

```bash
python scripts/raceshot_search.py -e "台北馬" -b 13213      # 用關鍵字搜尋
python scripts/raceshot_search.py -i 251203 -b 13213       # 用 event ID 搜尋
python scripts/raceshot_search.py -l -k "馬拉松"           # 列出馬拉松活動
```

| 參數 | 說明 |
|------|------|
| `--event, -e` | 活動名稱關鍵字 |
| `--bib, -b` | 號碼布號碼 |
| `--event-id, -i` | 活動 ID (直接指定) |
| `--list-events, -l` | 列出活動 |
| `--keyword, -k` | 過濾關鍵字 |
| `--limit, -n` | 最大活動數 (預設: 30) |
| `--json, -j` | JSON 輸出 |

**特點**:
- API 支援號碼布搜尋 (client-side 過濾)
- 單張照片價格: NT$169
- 活動照片數量可達數萬張，載入時間較長

## Dependencies

```bash
pip install requests beautifulsoup4
```

## Common Scenarios

### Scenario 1: User provides event + bib

User: "幫我搜尋高雄馬拉松號碼布 32319 的照片"

**Apply keyword optimization: "高雄馬拉松" → "高雄"**

Action: Search all platforms with short keyword
```bash
python ${SKILL_DIR}/scripts/phomi_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/goodshot_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/sportag_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/ctrun_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/allsports_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/zsport_search.py -e "高雄" -b 32319
python ${SKILL_DIR}/scripts/raceshot_search.py -e "高雄" -b 32319
```

### Scenario 2: User specifies platform

User: "在運動標籤找台北馬拉松 12345"

**Apply keyword optimization: "台北馬拉松" → "台北"**

Action: Search only Sportag
```bash
python ${SKILL_DIR}/scripts/sportag_search.py -e "台北" -b 12345
```

### Scenario 3: Browse available events

User: "有哪些馬拉松活動？"

Action: List events from all platforms
```bash
python ${SKILL_DIR}/scripts/phomi_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/goodshot_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/sportag_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/ctrun_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/allsports_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/zsport_search.py -l -k "馬拉松"
python ${SKILL_DIR}/scripts/raceshot_search.py -l -k "馬拉松"
```

### Scenario 4: Fallback when short keyword fails

User: "找萬金石馬拉松 8888"

**Step A: Try short keyword "萬金石" first**
```bash
python ${SKILL_DIR}/scripts/phomi_search.py -e "萬金石" -b 8888
# If no results...
```

**Step B: Fallback to original keyword**
```bash
python ${SKILL_DIR}/scripts/phomi_search.py -e "萬金石馬拉松" -b 8888
```

### Scenario 5: Multiple events found - 詢問日期

User: "找台北馬 13213"

搜尋 "台北馬" 後發現多個不同日期的活動：

**Action**: 詢問使用者日期
```
找到多個符合「台北馬」的活動，請問是哪一天的？
- 12/21 台北馬拉松（正式賽）
- 12/20 臺北馬拉松（耶誕歡樂早餐跑）
- 11/16 台北葡萄酒馬拉松
```

User: "12/21"

**Action**: 搜尋 12/21 的台北馬拉松（正式賽）

## Error Handling

| Error | Solution |
|-------|----------|
| "請先安裝必要套件" | `pip install requests beautifulsoup4` |
| "找不到符合的活動" | 使用更廣泛的關鍵字或列出活動 |
| "無法連線" | 檢查網路連線 |

## Reference Files

- `references/phomi-website.md` - Phomi 網站結構
- `references/goodshot-website.md` - GoodShot API 文件
- `references/sportag-website.md` - Sportag 網站結構
- `references/ctrun-website.md` - CTRun 網站結構
- `references/allsports-website.md` - AllSports 網站結構
- `references/zsport-website.md` - ZSport 網站結構
- `references/soonnet-website.md` - 捷安 (Soonnet Mall) 網站結構
- `references/soonnet-org-website.md` - 尋寶網 (Soonnet.org) 網站結構
- `references/raceshot-website.md` - 運動拍檔 (RaceShot) 網站結構
