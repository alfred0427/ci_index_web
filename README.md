# 📈 多市場多空綜合判斷系統（CI Market）
**CI Market — Multi-Market Composite Index System**  

一套基於 Python、GitHub、JavaScript 與 ECharts 所打造的「多市場量化多空分析系統」。  
本系統每日自動更新多市場（如 TW / US …）之 Buy/Sell 訊號、子指標 (subindex)、綜合指標 (composite index)，  
並用 GitHub Raw + 前端網頁呈現可交互、零後端的大盤多空儀表板。

---

# 📌 目錄
1. [系統介紹](#系統介紹)
2. [架構總覽](#架構總覽)
3. [後端運作流程（Python）](#後端運作流程python)
4. [自動更新流程（auto_updateps1）](#自動更新流程auto_updateps1)
5. [前端運作方式（index-copyhtml）](#前端運作方式index-copyhtml)
6. [資料夾結構](#資料夾結構)
7. [如何更換 GitHub 儲存帳號（重要）](#如何更換-github-儲存帳號重要)
8. [如何新增市場](#如何新增市場)
9. [使用者使用教學](#使用者使用教學)
10. [開發者操作流程](#開發者操作流程)

---

# 🌟 系統介紹
CI Market 用於：
- 整合多市場多空訊號（signals）
- 動態生成 subindex / composite index
- 計算市場恐懼－貪婪指標（ci_sell − ci_buy）
- 多市場儀表板呈現
- 自動更新資料到 GitHub（作為前端資料庫）

前端完全無後端需求，可部署於 GitHub Pages 或公司內部伺服器。

---

# 🧩 架構總覽

```
Python（main.py）
 ├── init：初始化所有指標
 ├── update：日常快速更新
 └── 寫出資料至 {market}_buy/sell_data/

GitHub Repository
 ├── 儲存所有 CSV + PNG
 └── 作為前端資料來源

index copy.html（前端）
 ├── 自動偵測市場
 ├── 總覽（多市場恐懼/貪婪指數）
 └── 個別市場 Buy/Sell Dashboard
```

---

# 🔧 後端運作流程（Python）

## ✔ init 模式 — “初始化所有東西”
```
python main.py fscore --market TW --mode init
```

功能：
- 重新挑選 top-n signals  
- 計算所有 subindex  
- 計算 composite index  
- 找出最佳 composite threshold  
- 生成所有 CSV、plot.png  
- 建立 config.json（供 update 模式使用）

## ✔ update 模式 — “每日快速更新”
```
python main.py fscore --market TW --mode update
```

功能：
- 讀取 config.json  
- 不重新選 signal  
- 不重新找 threshold  
- 只把新的行情資料更新  
- 生成新的 main_chart.csv、sub_*.csv

**update 模式速度非常快，適用於每日自動更新。**

---

# 🤖 自動更新流程（auto_update.ps1）

auto_update.ps1 可設定：

```powershell
$mode = "update"   # 每日更新
$mode = "init"     # 全部重算
```

並自動：
- 執行 main.py
- git add / commit / push
- 開啟 index copy.html

可設置 Windows Task Scheduler 每天自動更新。

---

# 🖥 前端運作方式（index copy.html）

## ✔ 總覽頁（Overview）
當網址沒有 `?market=` 時：

```
index copy.html
```

顯示：
- 多市場恐懼/貪婪折線圖（ci_sell - ci_buy）
- 多市場儀表圖（Gauge）
- 全部由 JS 直接讀取 GitHub Raw CSV 計算

## ✔ 個別市場頁（?market=TW）
當網址為：
```
index copy.html?market=TW
```

顯示：
- Buy 情境圖 plot.png  
- Buy main_chart.csv 表格  
- Buy 各 subindex 表格  
- Sell 情境圖 plot.png  
- Sell main_chart.csv 表格  
- Sell 各 subindex 表格  

## ✔ GitHub Raw + PapaParse + ECharts
前端透過：

- fetch() 讀取 GitHub Raw CSV  
- Papa.parse 解析  
- ECharts 畫圖  
- Bootstrap 呈現 UI  

完全無後端。

---

# 📁 資料夾結構

```
root/
│ index copy.html
│ main.py
│ auto_update.ps1
│ sn.csv / ms.csv / sn_dir.csv ...
│
├── TW_buy_data/
│     ├── config.json
│     ├── main_chart.csv
│     ├── plot.png
│     └── sub_*.csv
│
├── TW_sell_data/
│     └── ...
│
├── US_buy_data/
│     └── ...
└── US_sell_data/
      └── ...
```

---

# 🔑 如何更換 GitHub 儲存帳號（重要）

前端讀取來源寫在 index copy.html 中：

```javascript
const GH = {
  owner: 'alfred0427',
  repo: 'ci_index_web',
  branch: 'main'
};
```

若公司希望改為公司 GitHub：

### ✔ 第一步：修改成公司帳號
```javascript
const GH = {
  owner: 'COMPANY_GITHUB',
  repo: 'COMPANY_REPO',
  branch: 'main'
};
```

### ✔ 第二步：將所有資料搬到公司 repo
包含：
```
{market}_buy_data/
{market}_sell_data/
index copy.html
sn.csv / ms.csv / sub_signal.csv
```

### ✔ 第三步：將 auto_update.ps1 push 新 repo
update 系統會自動寫入新帳號的資料夾。

---

# ➕ 如何新增市場

以新增 JP 為例：

### ✔ Step 1：執行 init
```
python main.py fscore --market JP --mode init
```

會自動產生：
```
JP_buy_data/
JP_sell_data/
```

### ✔ Step 2：push
前端下拉選單會自動出現 JP。

---

# 📘 使用者使用教學

### ✔ 進入頁面（總覽）
```
index copy.html
```

顯示所有市場的恐懼/貪婪指數。

### ✔ 切換市場
右上角市場切換 → TW / US / JP…

### ✔ 查看 Buy/Sell
會出現：
- Buy/Sell 情境圖
- buy/sell 主表格
- 各 subindex

### ✔ 下載資料
按右上角「下載 CSV」可下載：
- main_chart.csv
- sub_*.csv
- ZIP 全部下載

---

# 🧑‍💻 開發者操作流程

### ✔ 更新 signal 或邏輯 → 跑 init
```
python main.py fscore --market TW --mode init
```

### ✔ 每日更新 → 跑 update
```
python main.py fscore --market TW --mode update
```

### ✔ 自動更新
執行：
```
.uto_update.ps1
```

---

# 🎯 結語
CI Market 以最輕量的技術堆疊提供多市場多空量化監控功能：

- 無伺服器  
- 多市場  
- 高度自動化  
- 易於維護  
- 適合企業內部量化研究與監控  

若需公司品牌客製化、Logo、額外儀表板、API 擴充，也可輕鬆加上。

---

*Produced by CI Market Backend & Frontend System.*
