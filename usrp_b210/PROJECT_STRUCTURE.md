# USRP B210 ISAC 專案結構

## 專案概述
本專案旨在開發基於USRP B210的28GHz ISAC（Integrated Sensing and Communications）系統，結合指向性天線陣列和beam forming技術，實現雷達感測與無線通訊的整合。

## 檔案結構

```
usrp_b210/
├── PROJECT_STRUCTURE.md     # 本檔案 - 專案結構說明
├── docs/                    # 📚 文檔資料夾
│   ├── README.md           # 專案主要說明文件
│   ├── development_plan.md # 開發計畫與時程
│   ├── algorithm_design.md # 詳細演算法設計
│   ├── algorithm_summary.md # 演算法摘要
│   ├── life_vital_signs_detection_memo.md # 生命體徵檢測備忘錄
│   └── TEST_README.md      # 測試指南
├── tests/                   # 🧪 測試腳本資料夾
│   ├── test_environment.py # 環境檢查測試
│   └── test_hardware.py    # 硬體功能測試
├── config/                  # ⚙️ 配置檔案資料夾
│   └── requirements.txt    # Python依賴套件清單
└── scripts/                # 📜 腳本資料夾 (待開發)
    └── (未來的執行腳本)
```

## 檔案分類說明

### 📚 docs/ - 文檔資料夾
**用途**: 存放所有專案文檔與設計資料
- **README.md**: 專案主要說明，快速入門指南
- **development_plan.md**: 8週開發計畫，包含階段目標與風險評估
- **algorithm_design.md**: 完整的演算法實作細節
- **algorithm_summary.md**: 核心演算法快速參考
- **life_vital_signs_detection_memo.md**: 非接觸式生命體徵檢測技術備忘錄
- **TEST_README.md**: 詳細測試指南與故障排除

### 🧪 tests/ - 測試腳本資料夾
**用途**: 存放所有測試相關程式碼
- **test_environment.py**: 檢查Linux環境、UHD、GNU Radio安裝
- **test_hardware.py**: B210硬體功能完整測試

### ⚙️ config/ - 配置檔案資料夾
**用途**: 存放系統配置與環境設定
- **requirements.txt**: Python依賴套件清單

### 📜 scripts/ - 腳本資料夾
**用途**: 存放可執行腳本與工具 (待開發)
- 未來將包含：
  - ISAC系統執行腳本
  - 自動化測試腳本
  - 部署工具

## 快速開始

### 1. 環境檢查
```bash
cd usrp_b210
python tests/test_environment.py
```

### 2. 硬體測試
```bash
python tests/test_hardware.py
```

### 3. 安裝依賴
```bash
pip install -r config/requirements.txt
```

### 4. 閱讀文檔
- 專案概述: `docs/README.md`
- 開發計畫: `docs/development_plan.md`
- 測試指南: `docs/TEST_README.md`

## 開發階段

### 當前階段: 階段1 - 硬體整合
- [x] 專案規劃與文檔建立
- [x] 測試腳本開發
- [ ] 硬體功能驗證
- [ ] 基礎信號處理
- [ ] 配置系統建立

### 下一階段: 階段2 - Beam-Aware ISAC
- [ ] Beam API整合
- [ ] 角度-距離聯合估測
- [ ] 自適應掃描策略
- [ ] 完整ISAC系統

## 技術重點

### 系統架構
- **硬體**: USRP B210 + Up/Down Converter + 28GHz RF + Beam Former
- **軟體**: Python 3.10+ + UHD 4.8+ + GNU Radio 3.10+
- **調變**: Chirp調變 (線性調頻)
- **頻寬**: 20MHz (B210限制)
- **距離解析度**: 7.5米

### 核心功能
1. **雷達感測**: 全方位掃描，角度-距離聯合估測
2. **無線通訊**: 定向通訊，Chirp參數編碼
3. **ISAC整合**: 時分複用，混合模式
4. **生命體徵檢測**: 微都卜勒技術 (未來擴展)

## 貢獻指南

### 檔案新增規則
- **文檔**: 新增到 `docs/`
- **測試**: 新增到 `tests/`
- **配置**: 新增到 `config/`
- **腳本**: 新增到 `scripts/`

### 命名規範
- **測試檔案**: `test_*.py`
- **配置檔案**: `*_config.*`
- **腳本檔案**: `run_*.py` 或 `*.sh`
- **文檔檔案**: `*.md`

### 更新此檔案
當專案結構有重大變更時，請更新本檔案以保持同步。

---

*專案結構最後更新: 2024年8月*
*TMYTEK ISAC Lab*
